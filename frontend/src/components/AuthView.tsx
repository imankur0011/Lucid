"use client";

import React, { useState } from "react";
import { BRAND } from "../lib/brand";
import { registerUser, loginWithCredentials, loginDemoUser, updateProfile, UserProfile } from "../lib/api";
import { IconLock, IconShield, IconAlertTriangle, IconBolt } from "./icons";

interface AuthViewProps {
  onSuccess: () => void;
  onCancel: () => void;
  onProfileUpdated?: (profile: UserProfile) => void;
}

export function AuthView({ onSuccess, onCancel, onProfileUpdated }: AuthViewProps) {
  const [mode, setMode] = useState<"register" | "login">("register");
  const [fullName, setFullName] = useState("");
  const [mobileNumber, setMobileNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    if (mode === "register") {
      if (!fullName.trim()) {
        setError("Please enter your name so we can personalize your portfolio.");
        return;
      }
      if (password.length < 6) {
        setError("Password must be at least 6 characters.");
        return;
      }
      if (!agreedToTerms) {
        setError("Please accept the fiduciary simulation terms to proceed.");
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === "register") {
        await registerUser(cleanEmail, password, mobileNumber.trim() || undefined);
        try {
          const updated = await updateProfile({
            display_name: fullName.trim(),
            mobile_number: mobileNumber.trim() || undefined,
          });
          if (onProfileUpdated) onProfileUpdated(updated);
        } catch {
          // Non-blocking profile name update
        }
      } else {
        await loginWithCredentials(cleanEmail, password);
      }
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed. Please check your credentials.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      await loginDemoUser();
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load demo account.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-8 space-y-6">
      {/* Return to Landing */}
      <button
        onClick={onCancel}
        type="button"
        className="text-xs font-semibold text-[#66758A] hover:text-[#142A3B] flex items-center gap-1.5 transition-colors cursor-pointer"
      >
        ← Back to Overview
      </button>

      {/* Auth Card */}
      <div className="bg-white rounded-2xl border border-[#E5E3DA] shadow-md p-6 sm:p-8 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-[#142A3B] text-white flex items-center justify-center font-bold text-xl mx-auto shadow-sm">
            {BRAND.symbol}
          </div>
          <h2 className="text-2xl font-editorial text-[#142A3B]">
            {mode === "register" ? "Create Your Investor Profile" : "Welcome Back"}
          </h2>
          <p className="text-xs text-[#66758A]">
            {mode === "register"
              ? "Start building your personalized, whole-share Indian stock portfolio."
              : "Access your saved portfolios, rebalance analysis, and order baskets."}
          </p>
        </div>

        {/* 1-Click Demo Shortcut */}
        <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-left">
            <div className="text-sm font-bold text-[#142A3B]">Want to test immediately?</div>
            <div className="text-xs sm:text-sm text-[#4A5568]">No sign-up or verification needed</div>
          </div>
          <button
            onClick={handleDemoLogin}
            disabled={loading}
            type="button"
            className="w-full sm:w-auto px-4 py-2 rounded-lg bg-[#285C4D] hover:bg-[#1E463A] text-white text-sm font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50 whitespace-nowrap flex items-center justify-center gap-1.5"
          >
            {loading ? (
              "Connecting..."
            ) : (
              <>
                <IconBolt className="w-3.5 h-3.5" />
                <span>Continue as Demo</span>
              </>
            )}
          </button>
        </div>

        <div className="relative flex items-center justify-center">
          <div className="border-t border-[#E5E3DA] w-full"></div>
          <span className="bg-white px-3 text-xs text-[#66758A] uppercase font-bold tracking-wider">
            or continue with email
          </span>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-xl bg-[#EFECE4] p-1 border border-[#E5E3DA]">
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
              mode === "register"
                ? "bg-white text-[#142A3B] shadow-xs"
                : "text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            Create Account
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
              mode === "login"
                ? "bg-white text-[#142A3B] shadow-xs"
                : "text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            Log In
          </button>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#B91C1C] text-xs flex items-center gap-2">
            <IconAlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <>
              <div>
                <label className="block text-xs font-semibold text-[#142A3B] mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Vikram Sharma"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-xs text-[#142A3B] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#142A3B]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#142A3B] mb-1.5">
                  Mobile Phone Number
                </label>
                <input
                  type="tel"
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  placeholder="e.g. +91 98765 43210"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-xs text-[#142A3B] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#142A3B]"
                />
                <span className="text-[10px] text-[#66758A] mt-1 block">
                  Used for OTP verification, two-factor authentication, and SEBI portfolio alerts.
                </span>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#142A3B] mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. vikram@example.com"
              className="w-full px-3.5 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-xs text-[#142A3B] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#142A3B]"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-semibold text-[#142A3B]">
                Password
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-xs text-[#4A5568] hover:text-[#142A3B] font-medium cursor-pointer"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-sm text-[#142A3B] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#142A3B]"
              />
            </div>
          </div>

          {mode === "register" && (
            <div className="flex items-start gap-2.5 pt-1">
              <input
                type="checkbox"
                id="terms"
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.target.checked)}
                className="mt-0.5 rounded border-[#D6D3C8] text-[#142A3B] focus:ring-[#142A3B] cursor-pointer"
              />
              <label htmlFor="terms" className="text-xs sm:text-sm text-[#4A5568] leading-relaxed cursor-pointer">
                I understand that {BRAND.name} provides simulated, non-custodial portfolio recommendations under SEBI (Investment Advisers) Regulations, 2013 standards.
              </label>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-sm font-bold transition-all shadow-sm cursor-pointer disabled:opacity-50"
          >
            {loading
              ? "Processing..."
              : mode === "register"
              ? "Create Profile & Continue →"
              : "Log In to Lucid →"}
          </button>
        </form>

        {/* Privacy Note */}
        <div className="flex items-center justify-center gap-1.5 text-xs text-[#66758A]">
          <IconShield className="w-4 h-4 text-[#285C4D]" />
          <span>Encrypted JWT Sessions & Fiduciary Protection</span>
        </div>
      </div>
    </div>
  );
}

