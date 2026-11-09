"use client";

import React, { useState } from "react";
import { BRAND, NavigationTab } from "../lib/brand";
import {
  IconShield,
  IconChartBar,
  IconLightbulb,
  IconRefresh,
  IconBolt,
  IconLock,
  IconMenu,
  IconX,
  IconUser,
  IconArrowUpRight,
  IconTrendingUp,
} from "./icons";
import { RiskAssessment } from "../lib/api";
import { NotificationsPanel } from "./NotificationsPanel";

interface NavbarProps {
  appView: "landing" | "auth" | "onboarding" | "dashboard";
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  assessment: RiskAssessment | null;
  onOpenAuthModal: () => void;
  onStartOnboarding: () => void;
  onGoToLanding: () => void;
  onGoToDashboard: () => void;
  onLogout: () => void;
  isAuthenticated: boolean;
  hasPortfolio: boolean;
}

export function Navbar({
  appView,
  activeTab,
  onTabChange,
  assessment,
  onOpenAuthModal,
  onStartOnboarding,
  onGoToLanding,
  onGoToDashboard,
  onLogout,
  isAuthenticated,
  hasPortfolio,
}: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabIcons: Record<string, React.ReactNode> = {
    results: <IconChartBar className="w-4 h-4" />,
    why: <IconLightbulb className="w-4 h-4" />,
    scenarios: <IconBolt className="w-4 h-4" />,
    diagnosis: <IconRefresh className="w-4 h-4" />,
    benchmarks: <IconTrendingUp className="w-4 h-4" />,
  };

  return (
    <header className="border-b border-[#E5E3DA] bg-[#FFFFFF]/95 backdrop-blur-md sticky top-0 z-50 transition-all">
      {/* Top Main Brand Header */}
      <div className="w-full max-w-[1440px] 2xl:max-w-[1536px] mx-auto px-4 sm:px-8 lg:px-12 h-16 flex items-center justify-between">
        {/* Brand Logo & Descriptor */}
        <div
          onClick={onGoToLanding}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-9 h-9 rounded-xl bg-[#142A3B] text-white flex items-center justify-center font-bold text-lg shadow-sm group-hover:bg-[#0E1E2B] transition-colors">
            {BRAND.symbol}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold tracking-tight text-lg sm:text-xl text-[#142A3B]">
                {BRAND.name}
              </span>
              <span className="hidden sm:inline-block text-xs px-2.5 py-0.5 rounded-full font-medium bg-[#EFECE4] text-[#4A5568] border border-[#E5E3DA]">
                {BRAND.version}
              </span>
            </div>
            <p className="text-xs text-[#66758A] font-medium hidden sm:block">
              {BRAND.descriptor}
            </p>
          </div>
        </div>

        {/* Right Action Controls depending on View */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Landing / Auth View Header Controls */}
          {appView === "landing" && (
            <div className="flex items-center gap-2 sm:gap-3">
              {hasPortfolio ? (
                <button
                  onClick={onGoToDashboard}
                  type="button"
                  className="px-4 py-2 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white text-sm font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1.5"
                >
                  <span>My Portfolio</span>
                  <IconArrowUpRight className="w-3.5 h-3.5" />
                </button>
              ) : null}

              <button
                onClick={onStartOnboarding}
                type="button"
                className="px-4.5 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-sm font-bold transition-all shadow-xs cursor-pointer"
              >
                {hasPortfolio ? "New Portfolio" : "Get Started"}
              </button>

              {isAuthenticated ? (
                <button
                  onClick={onOpenAuthModal}
                  type="button"
                  aria-label="Profile Account"
                  className="w-9 h-9 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] hover:border-[#D6D3C8] text-[#4A5568] flex items-center justify-center transition-colors cursor-pointer"
                  title="Investor Profile"
                >
                  <IconUser className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={onOpenAuthModal}
                  type="button"
                  className="px-3.5 py-2 rounded-xl border border-[#E5E3DA] text-sm font-semibold text-[#142A3B] hover:bg-[#F7F6F1] transition-colors cursor-pointer"
                >
                  Log In
                </button>
              )}
            </div>
          )}

          {/* Onboarding View Header Controls */}
          {appView === "onboarding" && (
            <div className="flex items-center gap-3">
              <span className="hidden sm:inline-block text-sm text-[#4A5568] font-medium">
                Investor Setup Wizard
              </span>
              <button
                onClick={onGoToLanding}
                type="button"
                className="text-sm font-bold text-[#66758A] hover:text-[#142A3B] px-3 py-1.5 rounded-lg hover:bg-[#F7F6F1] transition-colors cursor-pointer flex items-center gap-1.5"
              >
                <IconX className="w-3.5 h-3.5" />
                <span>Close</span>
              </button>
            </div>
          )}

          {/* Dashboard View Header Controls */}
          {appView === "dashboard" && (
            <div className="flex items-center gap-2 sm:gap-3">
              {/* Active Risk Profile Pill */}
              {assessment && (
                <div className="hidden md:flex items-center gap-1.5 text-xs bg-[#ECF3F0] border border-[#C6D8D1] px-3 py-1.5 rounded-lg text-[#285C4D] font-bold uppercase tracking-wide">
                  <IconShield className="w-3.5 h-3.5 text-[#285C4D]" />
                  <span>{assessment.risk_category.replace("_", " ")}</span>
                </div>
              )}

              {/* Create New Portfolio Button */}
              <button
                onClick={onStartOnboarding}
                type="button"
                className="px-4 py-2 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-sm font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                <span>+ New Portfolio</span>
              </button>

              {/* Notifications & Alert Bell */}
              <NotificationsPanel onNavigateTab={onTabChange} />

              {/* Profile & Account Trigger */}
              <button
                onClick={onOpenAuthModal}
                type="button"
                aria-label="User Account Profile"
                className="flex items-center gap-2 text-sm bg-[#F7F6F1] hover:bg-[#EFECE4] border border-[#E5E3DA] px-3.5 py-2 rounded-xl text-[#142A3B] transition-colors cursor-pointer"
                title="Investor Profile & Account"
              >
                <IconUser className="w-4 h-4 text-[#285C4D]" />
                <span className="font-semibold text-xs sm:text-sm">Profile</span>
              </button>

              {/* Logout Button */}
              <button
                onClick={onLogout}
                type="button"
                className="text-sm font-medium text-[#66758A] hover:text-[#B91C1C] px-2.5 py-1.5 rounded transition-colors cursor-pointer"
                title="Log Out"
              >
                Exit
              </button>

              {/* Mobile Menu Toggle */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                type="button"
                aria-label="Toggle navigation menu"
                className="lg:hidden p-2 rounded-lg bg-[#F7F6F1] border border-[#E5E3DA] text-[#142A3B]"
              >
                {mobileMenuOpen ? <IconX className="w-5 h-5" /> : <IconMenu className="w-5 h-5" />}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Secondary Bar: 4 Clean Tabs (Visible when in Dashboard View) */}
      {appView === "dashboard" && (
        <>
          <div className="hidden lg:flex w-full max-w-[1440px] 2xl:max-w-[1536px] mx-auto px-4 sm:px-8 lg:px-12 gap-8 text-sm font-medium border-t border-[#E5E3DA]">
            {BRAND.navItems.map((item) => {
              const tabKey = item.id as NavigationTab;
              const isActive = activeTab === tabKey;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(tabKey)}
                  type="button"
                  className={`py-3.5 border-b-2 transition-all flex items-center gap-2 cursor-pointer text-xs sm:text-sm ${
                    isActive
                      ? "border-[#142A3B] text-[#142A3B] font-bold"
                      : "border-transparent text-[#66758A] hover:text-[#142A3B]"
                  }`}
                >
                  <span className={isActive ? "text-[#285C4D]" : "text-[#66758A]"}>
                    {tabIcons[tabKey]}
                  </span>
                  <span>{item.label}</span>
                  {item.id === "scenarios" && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1] uppercase tracking-wider">
                      Live AI
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Mobile Drawer Navigation for Dashboard */}
          {mobileMenuOpen && (
            <div className="lg:hidden border-t border-[#E5E3DA] bg-white px-4 py-3 space-y-1 shadow-lg animate-fadeIn">
              {BRAND.navItems.map((item) => {
                const tabKey = item.id as NavigationTab;
                const isActive = activeTab === tabKey;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onTabChange(tabKey);
                      setMobileMenuOpen(false);
                    }}
                    type="button"
                    className={`w-full text-left px-3.5 py-2.5 rounded-xl text-sm font-medium flex items-center gap-2.5 transition-colors ${
                      isActive
                        ? "bg-[#F7F6F1] text-[#142A3B] font-bold border border-[#142A3B]"
                        : "text-[#4A5568] hover:bg-[#F7F6F1]"
                    }`}
                  >
                    <span className={isActive ? "text-[#285C4D]" : "text-[#66758A]"}>
                      {tabIcons[tabKey]}
                    </span>
                    <span>{item.label}</span>
                  {item.id === "scenarios" && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1] uppercase tracking-wider">
                      Live AI
                    </span>
                  )}
                  </button>
                );
              })}
            </div>
          )}
        </>
      )}
    </header>
  );
}
