const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

const dayFormatter = new Intl.DateTimeFormat('ja-JP', {
  month: 'numeric',
  day: 'numeric',
})

const yearFormatter = new Intl.DateTimeFormat('ja-JP', {
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
})

export function formatRelativeTime(
  iso: string,
  now: Date = new Date(),
): string {
  const then = new Date(iso)
  const diff = now.getTime() - then.getTime()

  if (Number.isNaN(diff)) return ''
  if (diff < MINUTE) return 'たった今'
  if (diff < HOUR) return `${Math.floor(diff / MINUTE)} 分前`
  if (diff < DAY) return `${Math.floor(diff / HOUR)} 時間前`
  if (diff < 2 * DAY) return '昨日'
  if (diff < 7 * DAY) return `${Math.floor(diff / DAY)} 日前`
  if (now.getFullYear() === then.getFullYear()) return dayFormatter.format(then)
  return yearFormatter.format(then)
}
