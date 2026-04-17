import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '~/components/ui/card'
import { Skeleton } from '~/components/ui/skeleton'

export function BlogCardSkeleton() {
  return (
    <Card aria-hidden className="shadow-none">
      <CardHeader className="flex flex-col gap-2">
        <CardTitle className="flex flex-col gap-2 font-normal">
          <Skeleton className="h-5 w-11/12" />
          <Skeleton className="h-5 w-full" />
        </CardTitle>
        <CardDescription className="flex flex-col gap-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </CardDescription>
      </CardHeader>
      <CardFooter className="flex w-full gap-3">
        <Skeleton className="h-3.5 flex-1" />
        <Skeleton className="h-3.5 flex-1" />
      </CardFooter>
    </Card>
  )
}

export function BlogListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <ul className="flex flex-col gap-4">
      {Array.from({ length: count }, (_, i) => (
        <li key={i}>
          <BlogCardSkeleton />
        </li>
      ))}
    </ul>
  )
}
