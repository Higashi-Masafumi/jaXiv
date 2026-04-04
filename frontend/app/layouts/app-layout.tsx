import { NavLink, Outlet } from 'react-router'
import { ArchiveIcon, FileTextIcon, SparklesIcon } from 'lucide-react'

import {
  Sidebar,
  SidebarContent,
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

const NAV_ITEMS = [
  { title: 'arXiv', url: '/', icon: SparklesIcon },
  { title: 'PDF', url: '/pdf', icon: FileTextIcon },
  { title: 'ブログ一覧', url: '/blog', icon: ArchiveIcon },
] as const

function AppSidebar() {
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
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
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
