import { LegalPage } from '~/components/legal-page'
import content from '../../../content/legal/terms.md?raw'

export function meta() {
  return [
    { title: '利用規約 | jaXiv' },
    { name: 'description', content: 'jaXiv の利用規約です。' },
  ]
}

export default function Terms() {
  return <LegalPage content={content} />
}
