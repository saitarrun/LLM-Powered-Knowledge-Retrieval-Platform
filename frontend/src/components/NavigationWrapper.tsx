"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "./Sidebar";

const SidebarContext = createContext({
  isOpen: false,
  toggle: () => {},
  close: () => {},
});

export const useSidebar = () => useContext(SidebarContext);

interface NavigationWrapperProps {
  children: React.ReactNode;
}

export default function NavigationWrapper({ children }: NavigationWrapperProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  const toggle = () => setIsOpen((v) => !v);
  const close = () => setIsOpen(false);

  const isLoginPage = pathname === "/login" || pathname === "/login/";

  useEffect(() => {
    if (isLoginPage) {
      setAuthChecked(true);
      return;
    }
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace("/login");
    } else {
      setAuthChecked(true);
    }
  }, [isLoginPage, router]);

  // On the login page — render without sidebar, no auth check needed
  if (isLoginPage) {
    return <>{children}</>;
  }

  // While checking auth, render nothing to avoid flash
  if (!authChecked) {
    return null;
  }

  return (
    <SidebarContext.Provider value={{ isOpen, toggle, close }}>
      <div className="flex h-full w-full relative overflow-hidden">
        {/* Fixed sidebar — desktop */}
        <Sidebar className="hidden md:flex fixed left-0 top-0 h-full" />

        {/* Mobile drawer overlay */}
        {isOpen && (
          <div className="md:hidden fixed inset-0 z-50 flex">
            <div
              className="fixed inset-0 bg-on-background/40 backdrop-blur-sm"
              onClick={close}
            />
            <div className="relative flex flex-col w-[280px] h-full bg-surface shadow-2xl z-10">
              <Sidebar className="flex h-full w-full" />
            </div>
          </div>
        )}

        {/* Main content — offset by sidebar width on desktop */}
        <div className="flex-1 md:ml-[280px] flex flex-col min-h-0 h-full overflow-hidden">
          {children}
        </div>
      </div>
    </SidebarContext.Provider>
  );
}
