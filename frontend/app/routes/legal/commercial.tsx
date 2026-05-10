import { LegalPage } from '~/components/legal-page'
import content from '../../../content/legal/commercial.md?raw'

export function meta() {
  return [
    { title: '特定商取引法に基づく表記 | jaXiv' },
    {
      name: 'description',
      content: 'jaXiv の特定商取引法に基づく表記です。',
    },
  ]
}

export default function Commercial() {
  return <LegalPage content={content} />
}
