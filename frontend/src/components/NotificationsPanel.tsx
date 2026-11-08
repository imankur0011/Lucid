"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  AppNotification,
  fetchNotifications,
  fetchUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
  dismissNotification,
} from "../lib/api";
import { BRAND, NavigationTab } from "../lib/brand";
import {
  IconBell,
  IconX,
  IconCheck,
  IconAlertTriangle,
  IconRefresh,
  IconShield,
  IconArrowUpRight,
  IconBolt,
  IconInfo,
} from "./icons";

interface NotificationsPanelProps {
  onNavigateTab?: (tab: NavigationTab) => void;
}

export function NotificationsPanel({ onNavigateTab }: NotificationsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const loadData = async () => {
    try {
      const [count, notifs] = await Promise.all([
        fetchUnreadNotificationCount(),
        fetchNotifications(false),
      ]);
      setUnreadCount(count);
      setNotifications(notifs);
    } catch {
      // Quiet fail in background polling
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const handleMarkRead = async (notifId: string) => {
    await markNotificationRead(notifId);
    setNotifications((prev) =>
      prev.map((n) => (n.notification_id === notifId ? { ...n, read_at: new Date().toISOString() } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  };

  const handleMarkAllRead = async () => {
    setLoading(true);
    await markAllNotificationsRead();
    const nowStr = new Date().toISOString();
    setNotifications((prev) => prev.map((n) => ({ ...n, read_at: n.read_at || nowStr })));
    setUnreadCount(0);
    setLoading(false);
  };

  const handleDismiss = async (e: React.MouseEvent, notifId: string) => {
    e.stopPropagation();
    await dismissNotification(notifId);
    const target = notifications.find((n) => n.notification_id === notifId);
    if (target && !target.read_at) {
      setUnreadCount((prev) => Math.max(0, prev - 1));
    }
    setNotifications((prev) => prev.filter((n) => n.notification_id !== notifId));
  };

  const handleNotificationClick = (notif: AppNotification) => {
    if (!notif.read_at) {
      handleMarkRead(notif.notification_id);
    }
    if (onNavigateTab) {
      const type = notif.notification_type;
      if (type.includes("drift") || type.includes("rebalance")) {
        onNavigateTab("diagnosis");
      } else if (type.includes("agent") || type.includes("regime")) {
        onNavigateTab("scenarios");
      } else {
        onNavigateTab("results");
      }
      setIsOpen(false);
    }
  };

  const formatTimeAgo = (isoString: string) => {
    if (!isoString) return "";
    try {
      const diffMs = Date.now() - new Date(isoString).getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch {
      return "";
    }
  };

  const getNotifIcon = (type: string) => {
    if (type.includes("drift") || type.includes("rebalance")) {
      return <IconRefresh className="w-4 h-4 text-[#D97706]" />;
    }
    if (type.includes("concentration") || type.includes("risk")) {
      return <IconAlertTriangle className="w-4 h-4 text-[#DC2626]" />;
    }
    if (type.includes("agent") || type.includes("regime")) {
      return <IconBolt className="w-4 h-4 text-[#285C4D]" />;
    }
    return <IconInfo className="w-4 h-4 text-[#142A3B]" />;
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell Trigger Button */}
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) loadData();
        }}
        type="button"
        aria-label="Open notifications"
        className="relative w-9 h-9 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] hover:border-[#D6D3C8] text-[#4A5568] flex items-center justify-center transition-colors cursor-pointer"
        title="Notifications & Portfolio Alerts"
      >
        <IconBell className="w-4.5 h-4.5 text-[#142A3B]" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 px-1.5 py-0.2 text-[10px] font-bold bg-[#DC2626] text-white rounded-full ring-2 ring-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-xl border border-[#E5E3DA] overflow-hidden z-50 animate-fadeIn">
          {/* Header */}
          <div className="px-4 py-3 bg-[#F7F6F1] border-b border-[#E5E3DA] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs uppercase tracking-wider text-[#142A3B]">
                Portfolio Alerts & Events
              </span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 text-[10px] font-extrabold bg-[#285C4D] text-white rounded-full">
                  {unreadCount} new
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                disabled={loading}
                className="text-[11px] font-semibold text-[#285C4D] hover:underline cursor-pointer"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-96 overflow-y-auto divide-y divide-[#EFECE4]">
            {notifications.length === 0 ? (
              <div className="py-10 px-4 text-center">
                <div className="w-10 h-10 rounded-full bg-[#ECF3F0] text-[#285C4D] mx-auto flex items-center justify-center mb-2">
                  <IconShield className="w-5 h-5" />
                </div>
                <p className="text-xs font-bold text-[#142A3B]">No New Alerts</p>
                <p className="text-[11px] text-[#66758A] mt-1">
                  Your portfolio holdings are operating within policy parameters.
                </p>
              </div>
            ) : (
              notifications.map((n) => {
                const isUnread = !n.read_at;
                return (
                  <div
                    key={n.notification_id}
                    onClick={() => handleNotificationClick(n)}
                    className={`p-3.5 transition-colors cursor-pointer flex gap-3 group relative ${
                      isUnread ? "bg-[#FFFBF5] hover:bg-[#FEF3C7]/40" : "hover:bg-[#F7F6F1]"
                    }`}
                  >
                    <div className="mt-0.5 flex-shrink-0">{getNotifIcon(n.notification_type)}</div>

                    <div className="flex-1 min-w-0 pr-4">
                      <div className="flex items-center justify-between gap-1">
                        <p
                          className={`text-xs truncate ${
                            isUnread ? "font-bold text-[#142A3B]" : "font-medium text-[#4A5568]"
                          }`}
                        >
                          {n.title}
                        </p>
                        <span className="text-[10px] text-[#94A3B8] whitespace-nowrap">
                          {formatTimeAgo(n.created_at)}
                        </span>
                      </div>

                      <p className="text-[11px] text-[#66758A] mt-0.5 line-clamp-2 leading-relaxed">
                        {n.message}
                      </p>

                      {/* Action Pill */}
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-[10px] font-semibold text-[#285C4D] flex items-center gap-1 group-hover:underline">
                          <span>Review Details</span>
                          <IconArrowUpRight className="w-3 h-3" />
                        </span>

                        {isUnread && (
                          <span className="w-2 h-2 rounded-full bg-[#DC2626]" title="Unread" />
                        )}
                      </div>
                    </div>

                    {/* Dismiss Button */}
                    <button
                      onClick={(e) => handleDismiss(e, n.notification_id)}
                      className="absolute top-2.5 right-2 p-1 text-[#94A3B8] hover:text-[#DC2626] rounded transition-colors opacity-0 group-hover:opacity-100"
                      title="Dismiss alert"
                    >
                      <IconX className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
