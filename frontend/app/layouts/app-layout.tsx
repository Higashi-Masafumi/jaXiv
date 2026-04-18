import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router'
import {
  ArchiveIcon,
  BookmarkIcon,
  FileTextIcon,
  LogInIcon,
  LogOutIcon,
  SparklesIcon,
} from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from '~/components/ui/sidebar'
import { Button } from '~/components/ui/button'

const NAV_ITEMS = [
  { title: 'arXiv', url: '/', icon: SparklesIcon },
  { title: 'PDF', url: '/pdf', icon: FileTextIcon },
  { title: 'ブログ一覧', url: '/blog', icon: ArchiveIcon },
] as const

function useGenerationCount(enabled: boolean, token: string | undefined) {
  const [count, setCount] = useState<{ monthly: number; limit: number } | null>(null)

  useEffect(() => {
    if (!enabled || !token) return
    fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/blog/my/generation-count`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => data && setCount({ monthly: data.monthly, limit: data.limit }))
      .catch(() => {})
  }, [enabled, token])

  return count
}

function AppSidebar() {
  const { user, isAnonymous, signInWithGoogle, signOut, session } = useAuth()
  const generationCount = useGenerationCount(!isAnonymous, session?.access_token)

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="flex flex-row items-center justify-between gap-2 px-4 py-3 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2">
        <span className="text-base font-black tracking-tight text-sidebar-foreground group-data-[collapsible=icon]:hidden">
          jaXiv
        </span>
        <SidebarTrigger
          className="shrink-0 text-sidebar-foreground group-data-[collapsible=icon]:mx-auto"
          aria-label="サイドバーを切り替え"
        />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map(item => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton asChild tooltip={item.title}>
                    <NavLink
                      to={item.url}
                      end
                      className={({ isActive }) =>
                        isActive
                          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                          : 'text-sidebar-foreground'
                      }
                    >
                      <item.icon />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}

              {/* マイブログ: ログイン済みユーザーのみ表示 */}
              {!isAnonymous && (
                <SidebarMenuItem>
                  <SidebarMenuButton asChild tooltip="マイブログ">
                    <NavLink
                      to="/my-blogs"
                      end
                      className={({ isActive }) =>
                        isActive
                          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                          : 'text-sidebar-foreground'
                      }
                    >
                      <BookmarkIcon />
                      <span>マイブログ</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-3 py-3">
        {isAnonymous ? (
          <Button
            variant="outline"
            size="sm"
            onClick={signInWithGoogle}
            className="w-full justify-start gap-2 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2"
          >
            <LogInIcon className="h-4 w-4 shrink-0" />
            <span className="group-data-[collapsible=icon]:hidden">
              ログイン
            </span>
          </Button>
        ) : (
          <div className="flex flex-col gap-1.5">
            <p className="truncate px-1 text-xs text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden">
              {user?.email ?? ''}
            </p>
            {generationCount && (
              <p className="px-1 text-xs text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden">
                今月の生成: {generationCount.monthly}/{generationCount.limit} 回
              </p>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={signOut}
              className="w-full justify-start gap-2 text-sidebar-foreground group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2"
            >
              <LogOutIcon className="h-4 w-4 shrink-0" />
              <span className="group-data-[collapsible=icon]:hidden">
                ログアウト
              </span>
            </Button>
          </div>
        )}
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}

/**
 * モバイルは Sheet のため、シートが閉じているときだけ開く用トリガーを出す。
 * デスクトップは collapsible="icon" で常にアイコン列が残るため不要。
 */
function AppMain() {
  const { isMobile, openMobile } = useSidebar()

  return (
    <div className="relative flex h-svh min-h-0 flex-1 flex-col overflow-hidden">
      {isMobile && !openMobile ? (
        <SidebarTrigger
          className="absolute left-3 top-3 z-50 size-9 shadow-md"
          variant="outline"
          aria-label="サイドバーを開く"
        />
      ) : null}
      <Outlet />
    </div>
  )
}

export default function AppLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <AppMain />
    </SidebarProvider>
  )
}
