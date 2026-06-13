import { NavLink, Outlet, useLocation } from 'react-router'
import {
  ArchiveIcon,
  BookmarkIcon,
  ChevronRightIcon,
  CrownIcon,
  FileTextIcon,
  ImagesIcon,
  LogInIcon,
  LogOutIcon,
  ScaleIcon,
  SparklesIcon,
} from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '~/components/ui/collapsible'
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
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
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
  { title: '図面提案', url: '/figures', icon: ImagesIcon },
] as const

const LEGAL_ITEMS = [
  { title: '利用規約', url: '/terms' },
  { title: 'プライバシーポリシー', url: '/privacy' },
  { title: '特商法表記', url: '/commercial' },
] as const

const NAV_ACTIVE_CLASS =
  'data-[active=true]:bg-primary/10 data-[active=true]:font-medium data-[active=true]:text-primary'

function isNavActive(pathname: string, url: string) {
  if (url === '/') return pathname === '/'
  return pathname === url || pathname.startsWith(`${url}/`)
}

function AppSidebar() {
  const { user, isAnonymous, isPaid, signInWithGoogle, signOut } = useAuth()
  const { pathname } = useLocation()
  const isLegalActive = LEGAL_ITEMS.some(item => item.url === pathname)

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="flex flex-row items-center justify-between gap-2 px-4 py-3.5 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2">
        <div className="flex items-center gap-2 group-data-[collapsible=icon]:hidden">
          <div className="flex size-6 items-center justify-center rounded-md bg-primary">
            <SparklesIcon className="size-3.5 text-primary-foreground" />
          </div>
          <span className="text-sm font-bold tracking-tight text-sidebar-foreground">
            jaXiv
          </span>
        </div>
        {/* icon モードではこのトリガーだけが表示される（mx-auto で中央配置） */}
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
                  <SidebarMenuButton
                    asChild
                    isActive={isNavActive(pathname, item.url)}
                    tooltip={item.title}
                    className={NAV_ACTIVE_CLASS}
                  >
                    <NavLink to={item.url} end>
                      <item.icon />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}

              {!isAnonymous && (
                <SidebarMenuItem>
                  <SidebarMenuButton
                    asChild
                    isActive={isNavActive(pathname, '/my-blogs')}
                    tooltip="マイブログ"
                    className={NAV_ACTIVE_CLASS}
                  >
                    <NavLink to="/my-blogs" end>
                      <BookmarkIcon />
                      <span>マイブログ</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )}

              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={isNavActive(pathname, '/pricing')}
                  tooltip={isPaid ? 'プラン管理' : 'アップグレード'}
                  className={NAV_ACTIVE_CLASS}
                >
                  <NavLink to="/pricing" end>
                    <CrownIcon />
                    <span>{isPaid ? 'プラン管理' : 'アップグレード'}</span>
                  </NavLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-3 py-3">
        <Collapsible defaultOpen={isLegalActive} className="group/legal">
          <SidebarMenu>
            <SidebarMenuItem>
              <CollapsibleTrigger asChild>
                <SidebarMenuButton tooltip="法的情報">
                  <ScaleIcon />
                  <span>法的情報</span>
                  <ChevronRightIcon className="ml-auto transition-transform group-data-[state=open]/legal:rotate-90" />
                </SidebarMenuButton>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <SidebarMenuSub>
                  {LEGAL_ITEMS.map(item => (
                    <SidebarMenuSubItem key={item.url}>
                      <SidebarMenuSubButton
                        asChild
                        isActive={pathname === item.url}
                        className="data-[active=true]:font-medium data-[active=true]:text-primary"
                      >
                        <NavLink to={item.url}>{item.title}</NavLink>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  ))}
                </SidebarMenuSub>
              </CollapsibleContent>
            </SidebarMenuItem>
          </SidebarMenu>
        </Collapsible>

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
