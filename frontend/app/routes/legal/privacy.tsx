import { LegalPage } from '~/components/legal-page'
import content from '../../../content/legal/privacy.md?raw'

export function meta() {
  return [
    { title: 'プライバシーポリシー | jaXiv' },
    { name: 'description', content: 'jaXiv のプライバシーポリシーです。' },
  ]
}

export default function Privacy() {
  return <LegalPage content={content} />
}
