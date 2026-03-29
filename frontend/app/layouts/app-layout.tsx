import { NavLink, Outlet } from 'react-router'
import { ArchiveIcon, SparklesIcon } from 'lucide-react'

import { Separator } from '~/components/ui/separator'
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
  SidebarTrigger,
} from '~/components/ui/sidebar'

const NAV_ITEMS = [
  { title: 'ブログ生成', url: '/', icon: SparklesIcon },
  { title: 'アーカイブ', url: '/archive', icon: ArchiveIcon },
] as const

function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="px-4 py-3">
        <span className="text-base font-black tracking-tight text-sidebar-foreground">
          jaXiv
        </span>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton asChild>
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
    </Sidebar>
  )
}

export default function AppLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-border bg-background px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="h-4" />
          <span className="text-sm font-semibold text-foreground">jaXiv</span>
        </header>
        <Outlet />
      </div>
    </SidebarProvider>
  )
}
