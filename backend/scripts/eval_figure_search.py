"""Offline precision evaluation for figure search modes.

Compares the three figure retrieval strategies on a labelled query set so we can
decide, on jaXiv's *actual* corpus, whether scoring against image embeddings
helps over the caption-only baseline:

  - ``caption`` : nomic-embed-text caption vector (the previous behaviour)
  - ``image``   : nomic-embed-vision image vector
  - ``hybrid``  : reciprocal-rank fusion of both (the new default)

The query is always a nomic-embed-text vector; it is comparable to the image
vectors because nomic-embed-vision shares one latent space with the text model.

Usage (from the ``backend`` directory, against a running Qdrant + pdf_analysis):

    uv run python -m scripts.eval_figure_search --dataset scripts/figure_search_eval.json

Dataset format (JSON): a list of objects, each with a free-form ``query`` and the
``relevant_image_urls`` that a good search should surface for it. Build it from
real figures in your Qdrant collection (their ``image_url`` payload values):

    [
      {
        "query": "transformer self-attention architecture diagram",
        "relevant_image_urls": [
          "https://.../figure-3.png",
          "https://.../figure-4.png"
        ]
      }
    ]

Metrics are macro-averaged over queries: Recall@k, nDCG@k, and MRR.
"""

import argparse
import asyncio
import json
import math
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from domain.repositories.i_figure_chunk_repository import FigureSearchMode
from infrastructure.layout_analysis import HttpQueryEmbeddingGateway
from infrastructure.qdrant import QdrantFigureChunkRepository

SCRIPT_DIR = Path(__file__).resolve().parent
ALL_MODES: tuple[FigureSearchMode, ...] = ('caption', 'image', 'hybrid')


class EvalCase(BaseModel):
	model_config = ConfigDict(frozen=True)

	query: str = Field(min_length=1)
	relevant_image_urls: list[str] = Field(min_length=1)


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
	top = ranked[:k]
	found = sum(1 for url in top if url in relevant)
	return found / len(relevant)


def ndcg_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
	dcg = sum(1.0 / math.log2(i + 2) for i, url in enumerate(ranked[:k]) if url in relevant)
	ideal_hits = min(len(relevant), k)
	idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
	return dcg / idcg if idcg else 0.0


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
	for i, url in enumerate(ranked):
		if url in relevant:
			return 1.0 / (i + 1)
	return 0.0


def load_dataset(path: Path) -> list[EvalCase]:
	raw = json.loads(path.read_text(encoding='utf-8'))
	return [EvalCase.model_validate(item) for item in raw]


async def evaluate(
	dataset: list[EvalCase],
	modes: list[FigureSearchMode],
	ks: list[int],
) -> dict[FigureSearchMode, dict[str, float]]:
	gateway = HttpQueryEmbeddingGateway()
	repository = QdrantFigureChunkRepository()
	depth = max(ks)

	# Accumulate metric sums per mode, then macro-average over the query set.
	sums: dict[FigureSearchMode, dict[str, float]] = {
		mode: {f'recall@{k}': 0.0 for k in ks} for mode in modes
	}
	for mode in modes:
		for k in ks:
			sums[mode][f'ndcg@{k}'] = 0.0
		sums[mode]['mrr'] = 0.0

	for case in dataset:
		# Query embedding is mode-independent (always nomic-embed-text), embed once.
		emb = await gateway.embed_query(case.query, 'nomic')
		relevant = set(case.relevant_image_urls)
		for mode in modes:
			hits = await repository.query_global(emb, mode=mode, limit=depth)
			ranked = [hit.image_url for hit in hits]
			for k in ks:
				sums[mode][f'recall@{k}'] += recall_at_k(ranked, relevant, k)
				sums[mode][f'ndcg@{k}'] += ndcg_at_k(ranked, relevant, k)
			sums[mode]['mrr'] += reciprocal_rank(ranked, relevant)

	n = len(dataset)
	return {
		mode: {metric: total / n for metric, total in metrics.items()}
		for mode, metrics in sums.items()
	}


def print_report(
	results: dict[FigureSearchMode, dict[str, float]],
	modes: list[FigureSearchMode],
	ks: list[int],
	n_cases: int,
) -> None:
	metric_names = [f'recall@{k}' for k in ks] + [f'ndcg@{k}' for k in ks] + ['mrr']
	header = f'{"metric":<12}' + ''.join(f'{mode:>12}' for mode in modes)
	print(f'\nFigure search evaluation ({n_cases} queries)\n')
	print(header)
	print('-' * len(header))
	for metric in metric_names:
		row = f'{metric:<12}'
		best = max(results[mode][metric] for mode in modes)
		for mode in modes:
			value = results[mode][metric]
			marker = '*' if value == best and best > 0 else ' '
			row += f'{value:>11.4f}{marker}'
		print(row)
	print('\n(* = best per row)')


async def _main(args: argparse.Namespace) -> None:
	dataset_path = Path(args.dataset)
	if not dataset_path.is_absolute():
		dataset_path = Path.cwd() / dataset_path
	dataset = load_dataset(dataset_path)
	if not dataset:
		raise SystemExit(f'No evaluation cases found in {dataset_path}')

	ks = sorted({int(k) for k in args.ks.split(',')})
	modes = [mode.strip() for mode in args.modes.split(',')]
	invalid = [m for m in modes if m not in ALL_MODES]
	if invalid:
		raise SystemExit(f'Unknown mode(s): {invalid}. Choose from {list(ALL_MODES)}')

	results = await evaluate(dataset, modes, ks)  # type: ignore[arg-type]
	print_report(results, modes, ks, len(dataset))  # type: ignore[arg-type]


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		'--dataset',
		default=str(SCRIPT_DIR / 'figure_search_eval.json'),
		help='Path to the labelled query JSON file.',
	)
	parser.add_argument(
		'--modes',
		default='caption,image,hybrid',
		help='Comma-separated subset of: caption,image,hybrid.',
	)
	parser.add_argument(
		'--ks',
		default='5,10',
		help='Comma-separated cutoffs for Recall@k / nDCG@k.',
	)
	asyncio.run(_main(parser.parse_args()))


if __name__ == '__main__':
	main()
