"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  UserProfile,
  AppUser,
  FinancialGoal,
  RiskAssessment,
  PortfolioVersion,
  PortfolioSummary,
  fetchCurrentUser,
  fetchProfile,
  fetchPortfolios,
  updateProfile,
  requestVerification,
  verifyCode,
  changePassword,
  logoutUser,
  exportUserData,
  deleteAccount,
} from "../lib/api";
import {
  IconLock,
  IconUser,
  IconX,
  IconCheck,
  IconShield,
  IconLightbulb,
  IconLayers,
  IconAlertTriangle,
  IconMail,
  IconPhone,
  IconEdit,
  IconArrowRight,
  IconTrash,
  IconDownloadCloud,
  IconAlertCircle,
} from "./icons";
import { DeletePortfolioModal } from "./DeletePortfolioModal";

interface ProfileAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: UserProfile | null;
  goals: FinancialGoal[];
  jwtToken: string | null;
  onTokenUpdated: (token: string | null) => void;
  assessment?: RiskAssessment | null;
  onStartOnboarding?: () => void;
  onLogout?: () => void;
  activePortfolio?: PortfolioVersion | null;
  allPortfolios?: PortfolioSummary[];
  onPortfolioDeleted?: () => void;
}

type AccountTab = "profile" | "preferences" | "security" | "connected" | "account";

export function ProfileAuthModal({
  isOpen,
  onClose,
  profile,
  goals,
  jwtToken,
  onTokenUpdated,
  assessment,
  onStartOnboarding,
  onLogout,
  activePortfolio,
  allPortfolios,
  onPortfolioDeleted,
}: ProfileAuthModalProps) {
  const [activeTab, setActiveTab] = useState<AccountTab>("profile");

  // User account state from /auth/me and /profile
  const [currentUser, setCurrentUser] = useState<AppUser | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(profile);
  const [loadingUser, setLoadingUser] = useState(false);

  // Edit Profile mode state
  const [isEditing, setIsEditing] = useState(false);
  const [displayNameInput, setDisplayNameInput] = useState("");
  const [mobileInput, setMobileInput] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Edit Preferences mode state
  const [isEditingPreferences, setIsEditingPreferences] = useState(false);
  const [prefExpInput, setPrefExpInput] = useState<string>("beginner");
  const [prefKnowledgeInput, setPrefKnowledgeInput] = useState<string>("basic");
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [preferencesMessage, setPreferencesMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Verification state (Email / Mobile OTP)
  const [verifyType, setVerifyType] = useState<"email_verification" | "mobile_verification">("email_verification");
  const [verifyRecipient, setVerifyRecipient] = useState("");
  const [verifyCodeInput, setVerifyCodeInput] = useState("");
  const [verifyRequested, setVerifyRequested] = useState(false);
  const [verifyDemoCode, setVerifyDemoCode] = useState<string | null>(null);
  const [verifyStatusMessage, setVerifyStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  // Change Password state
  const [currentPasswordInput, setCurrentPasswordInput] = useState("");
  const [newPasswordInput, setNewPasswordInput] = useState("");
  const [confirmPasswordInput, setConfirmPasswordInput] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordStatusMessage, setPasswordStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Account & Data Management state
  const [accountDeletePassword, setAccountDeletePassword] = useState("");
  const [accountDeletePhrase, setAccountDeletePhrase] = useState("");
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [accountDeleteError, setAccountDeleteError] = useState<string | null>(null);
  const [accountDeleteSuccess, setAccountDeleteSuccess] = useState(false);
  const [isExportingData, setIsExportingData] = useState(false);
  const [exportSuccessMessage, setExportSuccessMessage] = useState<string | null>(null);
  const [exportErrorMessage, setExportErrorMessage] = useState<string | null>(null);

  // Portfolio Management & Deletion state
  const [portfoliosList, setPortfoliosList] = useState<PortfolioSummary[]>(allPortfolios || []);
  const [selectedPortfolioIds, setSelectedPortfolioIds] = useState<string[]>([]);
  const [deleteTargets, setDeleteTargets] = useState<PortfolioSummary[]>([]);
  const [isDeleteAllMode, setIsDeleteAllMode] = useState<boolean>(false);
  const [isDeletePortfolioModalOpen, setIsDeletePortfolioModalOpen] = useState(false);
  const [portfolioNotice, setPortfolioNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Sync portfolios list with parent prop
  useEffect(() => {
    if (allPortfolios) {
      setPortfoliosList(allPortfolios);
    }
  }, [allPortfolios]);

  // Load fresh portfolios when tab switches to account
  const refreshPortfolios = useCallback(async () => {
    try {
      const data = await fetchPortfolios();
      setPortfoliosList(data);
    } catch {
      // Non-blocking
    }
  }, []);

  useEffect(() => {
    if (isOpen && activeTab === "account") {
      refreshPortfolios();
    }
  }, [isOpen, activeTab, refreshPortfolios]);

  // Portfolio Selection Handlers
  const handleToggleSelectPortfolio = (id: string) => {
    setSelectedPortfolioIds((prev) =>
      prev.includes(id) ? prev.filter((pId) => pId !== id) : [...prev, id]
    );
  };

  const handleToggleSelectAll = () => {
    if (selectedPortfolioIds.length === portfoliosList.length) {
      setSelectedPortfolioIds([]);
    } else {
      setSelectedPortfolioIds(portfoliosList.map((p) => p.portfolio_id));
    }
  };

  const handleRequestDeleteSingle = (p: PortfolioSummary) => {
    setDeleteTargets([p]);
    setIsDeleteAllMode(false);
    setIsDeletePortfolioModalOpen(true);
  };

  const handleRequestDeleteSelected = () => {
    const targets = portfoliosList.filter((p) => selectedPortfolioIds.includes(p.portfolio_id));
    if (targets.length === 0) return;
    setDeleteTargets(targets);
    setIsDeleteAllMode(false);
    setIsDeletePortfolioModalOpen(true);
  };

  const handleRequestDeleteAll = () => {
    if (portfoliosList.length === 0) return;
    setDeleteTargets(portfoliosList);
    setIsDeleteAllMode(true);
    setIsDeletePortfolioModalOpen(true);
  };

  const handlePortfoliosDeleted = async () => {
    const count = isDeleteAllMode ? portfoliosList.length : deleteTargets.length;
    setSelectedPortfolioIds([]);
    setDeleteTargets([]);
    setIsDeleteAllMode(false);
    setPortfolioNotice({
      type: "success",
      text: `Successfully deleted ${count} portfolio${count > 1 ? "s" : ""}.`,
    });
    await refreshPortfolios();
    if (onPortfolioDeleted) onPortfolioDeleted();
  };

  // Keep userProfile synced with parent profile prop
  useEffect(() => {
    if (profile) {
      setUserProfile(profile);
      setPrefExpInput((profile.investment_experience || "beginner").toLowerCase());
      setPrefKnowledgeInput((profile.investment_knowledge_level || "basic").toLowerCase());
    }
  }, [profile]);

  // Load authenticated user details on modal open
  const loadUser = useCallback(async () => {
    setLoadingUser(true);
    try {
      const [u, p] = await Promise.all([
        fetchCurrentUser().catch(() => null),
        fetchProfile().catch(() => null),
      ]);
      if (u) {
        setCurrentUser(u);
        setDisplayNameInput(u.profile?.display_name || p?.display_name || profile?.display_name || "Investor");
        setMobileInput(u.mobile_number || u.profile?.mobile_number || p?.mobile_number || profile?.mobile_number || "");
        setVerifyRecipient(u.email || "");
      }
      if (p) {
        setUserProfile(p);
        setPrefExpInput((p.investment_experience || "beginner").toLowerCase());
        setPrefKnowledgeInput((p.investment_knowledge_level || "basic").toLowerCase());
      } else if (u?.profile) {
        setUserProfile(u.profile);
        setPrefExpInput((u.profile.investment_experience || "beginner").toLowerCase());
        setPrefKnowledgeInput((u.profile.investment_knowledge_level || "basic").toLowerCase());
      } else if (profile) {
        setUserProfile(profile);
        setPrefExpInput((profile.investment_experience || "beginner").toLowerCase());
        setPrefKnowledgeInput((profile.investment_knowledge_level || "basic").toLowerCase());
      }
    } catch {
      // Fallback to local profile props
      setDisplayNameInput(profile?.display_name || "Investor");
      setMobileInput(profile?.mobile_number || "");
      if (profile) {
        setUserProfile(profile);
        setPrefExpInput((profile.investment_experience || "beginner").toLowerCase());
        setPrefKnowledgeInput((profile.investment_knowledge_level || "basic").toLowerCase());
      }
    } finally {
      setLoadingUser(false);
    }
  }, [profile]);

  useEffect(() => {
    if (isOpen) {
      loadUser();
      setIsEditing(false);
      setIsEditingPreferences(false);
      setProfileMessage(null);
      setPreferencesMessage(null);
      setPasswordStatusMessage(null);
      setVerifyStatusMessage(null);
    }
  }, [isOpen, loadUser]);

  if (!isOpen) return null;

  // Handle Edit Profile Save
  const handleSaveProfile = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSavingProfile(true);
    setProfileMessage(null);
    try {
      const updated = await updateProfile({
        display_name: displayNameInput.trim() || undefined,
        mobile_number: mobileInput.trim() || undefined,
      });
      setUserProfile(updated);
      setIsEditing(false);
      setProfileMessage({ type: "success", text: "Your profile information has been updated." });
      if (currentUser) {
        setCurrentUser({
          ...currentUser,
          mobile_number: mobileInput.trim() || currentUser.mobile_number,
          profile: updated,
        });
      }
      onTokenUpdated(jwtToken);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save profile changes";
      setProfileMessage({ type: "error", text: msg });
    } finally {
      setSavingProfile(false);
    }
  };

  // Handle Edit Investment Preferences Save
  const handleSavePreferences = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSavingPreferences(true);
    setPreferencesMessage(null);
    try {
      const updated = await updateProfile({
        investment_experience: prefExpInput as "beginner" | "intermediate" | "experienced",
        investment_knowledge_level: prefKnowledgeInput as "basic" | "intermediate" | "advanced",
      });
      setUserProfile(updated);
      setIsEditingPreferences(false);
      setPreferencesMessage({
        type: "success",
        text: "Investment preferences updated successfully.",
      });
      if (currentUser) {
        setCurrentUser({
          ...currentUser,
          profile: updated,
        });
      }
      onTokenUpdated(jwtToken);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update investment preferences";
      setPreferencesMessage({ type: "error", text: msg });
    } finally {
      setSavingPreferences(false);
    }
  };

  // Handle Verification OTP Request
  const handleRequestVerification = async () => {
    setIsVerifying(true);
    setVerifyStatusMessage(null);
    const targetRecipient = verifyRecipient.trim() || (verifyType === "email_verification" ? (currentUser?.email || "") : (currentUser?.mobile_number || mobileInput || ""));
    if (!targetRecipient) {
      setVerifyStatusMessage({
        type: "error",
        text: verifyType === "email_verification"
          ? "Please provide a registered email address to send the verification code."
          : "Please provide a mobile phone number to send the SMS verification code.",
      });
      setIsVerifying(false);
      return;
    }

    try {
      const res = await requestVerification(targetRecipient, verifyType);
      setVerifyRequested(true);
      setVerifyDemoCode(res.demo_code || null);
      if (res.demo_code) setVerifyCodeInput(res.demo_code);
      setVerifyStatusMessage({ type: "success", text: res.message || `Verification code sent to ${targetRecipient}` });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to send verification code";
      setVerifyStatusMessage({ type: "error", text: msg });
    } finally {
      setIsVerifying(false);
    }
  };

  // Handle Verification OTP Submission
  const handleVerifyCode = async () => {
    setIsVerifying(true);
    setVerifyStatusMessage(null);
    const targetRecipient = verifyRecipient.trim() || (verifyType === "email_verification" ? (currentUser?.email || "") : (currentUser?.mobile_number || mobileInput || ""));
    try {
      const res = await verifyCode(targetRecipient, verifyCodeInput.trim(), verifyType);
      setVerifyStatusMessage({
        type: "success",
        text: res.message || `${verifyType === "email_verification" ? "Email" : "Mobile number"} verified successfully!`,
      });
      setVerifyRequested(false);
      setVerifyDemoCode(null);
      setVerifyCodeInput("");
      await loadUser();
      onTokenUpdated(jwtToken);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Invalid or expired verification code";
      setVerifyStatusMessage({ type: "error", text: msg });
    } finally {
      setIsVerifying(false);
    }
  };

  // Handle Change Password Submission
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordStatusMessage(null);

    if (newPasswordInput.length < 6) {
      setPasswordStatusMessage({ type: "error", text: "New password must be at least 6 characters long." });
      return;
    }
    if (newPasswordInput !== confirmPasswordInput) {
      setPasswordStatusMessage({ type: "error", text: "New password and confirmation do not match." });
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await changePassword(newPasswordInput, currentPasswordInput || undefined);
      setPasswordStatusMessage({ type: "success", text: res.message || "Password updated successfully." });
      setCurrentPasswordInput("");
      setNewPasswordInput("");
      setConfirmPasswordInput("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update password. Please verify current password.";
      setPasswordStatusMessage({ type: "error", text: msg });
    } finally {
      setIsChangingPassword(false);
    }
  };

  // Handle Sign Out
  const handleSignOut = async () => {
    try {
      await logoutUser();
    } catch {
      // Ignore network errors on logout
    }
    onTokenUpdated(null);
    if (onLogout) onLogout();
    onClose();
  };

  // Handle Export Data
  const handleExportData = async () => {
    setIsExportingData(true);
    setExportErrorMessage(null);
    setExportSuccessMessage(null);
    try {
      const data = await exportUserData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `lucid_data_export_${currentUser?.user_id || "investor"}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportSuccessMessage("Your complete Lucid investor data archive has been downloaded.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to export data";
      setExportErrorMessage(msg);
    } finally {
      setIsExportingData(false);
    }
  };

  // Handle Permanent Account Deletion
  const handlePermanentAccountDeletion = async () => {
    if (accountDeletePhrase.trim().toUpperCase() !== "DELETE MY ACCOUNT") {
      setAccountDeleteError("Please type 'DELETE MY ACCOUNT' exactly to confirm.");
      return;
    }
    setIsDeletingAccount(true);
    setAccountDeleteError(null);
    try {
      await deleteAccount({
        password: accountDeletePassword || undefined,
        confirmationPhrase: accountDeletePhrase.trim(),
      });
      setAccountDeleteSuccess(true);
      setTimeout(() => {
        onTokenUpdated(null);
        if (onLogout) onLogout();
        onClose();
      }, 1500);
    } catch (err: unknown) {
      setIsDeletingAccount(false);
      const msg = err instanceof Error ? err.message : "Failed to delete account";
      setAccountDeleteError(msg);
    }
  };

  // Helper date formatter
  const formattedMemberSince = currentUser?.created_at
    ? new Date(currentUser.created_at).toLocaleDateString("en-IN", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "October 2026";

  const emailDisplay = currentUser?.email || "";
  const mobileDisplay = currentUser?.mobile_number || userProfile?.mobile_number || mobileInput || "";
  const nameDisplay = userProfile?.display_name || currentUser?.profile?.display_name || profile?.display_name || "Investor";
  const primaryGoal = goals && goals.length > 0 ? goals[0] : null;

  const EXPERIENCE_CONFIG: Record<string, { label: string; desc: string }> = {
    beginner: {
      label: "Beginner",
      desc: "New to direct equities; prioritizing established large-caps and capital protection.",
    },
    intermediate: {
      label: "Intermediate",
      desc: "Familiar with mutual funds and equities; seeking disciplined factor growth.",
    },
    experienced: {
      label: "Experienced",
      desc: "Active equity participant with verified market cycle familiarity.",
    },
  };

  const KNOWLEDGE_CONFIG: Record<string, { label: string; desc: string }> = {
    basic: {
      label: "Basic / Beginner",
      desc: "Primary background in bank deposits, fixed income, or mutual fund SIPs.",
    },
    intermediate: {
      label: "Intermediate",
      desc: "Understands balance sheets, index benchmarks, and diversification principles.",
    },
    advanced: {
      label: "Advanced",
      desc: "Understands standard deviation, drawdowns, and fundamental financial statements.",
    },
  };

  const RISK_CONFIG: Record<string, { label: string; vol: string; desc: string }> = {
    very_conservative: {
      label: "Very Conservative",
      vol: "8.0% Target Volatility",
      desc: "Prioritizes capital protection with minimal price volatility and resilient dividend leaders.",
    },
    conservative: {
      label: "Conservative",
      vol: "10.0% Target Volatility",
      desc: "Lower-volatility equity allocation focused on established large-cap bluechips.",
    },
    moderate: {
      label: "Moderate",
      vol: "12.5% Target Volatility",
      desc: "Balanced portfolio balancing capital growth with defensive sector allocation.",
    },
    growth: {
      label: "Growth",
      vol: "15.0% Target Volatility",
      desc: "Optimized for capital compounding with high Sharpe ratio quality leaders.",
    },
    aggressive: {
      label: "Aggressive",
      vol: "18.0% Target Volatility",
      desc: "High-conviction growth equities engineered for maximum long-term capital appreciation.",
    },
  };

  const activeExp = (
    userProfile?.investment_experience ||
    currentUser?.profile?.investment_experience ||
    profile?.investment_experience ||
    "beginner"
  ).toLowerCase();

  const activeKnowledge = (
    userProfile?.investment_knowledge_level ||
    currentUser?.profile?.investment_knowledge_level ||
    profile?.investment_knowledge_level ||
    "basic"
  ).toLowerCase();

  const currentRiskConfig =
    RISK_CONFIG[(assessment?.risk_category || "growth").toLowerCase()] ||
    RISK_CONFIG.growth;

  return (
    <div className="fixed inset-0 z-50 bg-[#142A3B]/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fadeIn">
      <div className="bg-white border border-[#E5E3DA] rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative my-8 transition-all">
        {/* Header */}
        <div className="flex justify-between items-start pb-4 border-b border-[#E5E3DA]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-[#166534] uppercase tracking-wider">
                Lucid Investor Account
              </span>
              <span className="text-[#94A3B8]">&bull;</span>
              <span className="text-xs text-[#66758A]">
                Account Settings &amp; Preferences
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-[#142A3B] flex items-center gap-2.5">
              <IconUser className="w-5 h-5 text-[#285C4D]" />
              <span>Investor Profile &amp; Account</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            type="button"
            aria-label="Close Account Modal"
            className="p-2 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] hover:border-[#D6D3C8] text-[#66758A] hover:text-[#142A3B] transition-colors cursor-pointer"
          >
            <IconX className="w-5 h-5" />
          </button>
        </div>

        {/* Account Tab Navigation */}
        <div className="flex border-b border-[#E5E3DA] mt-4 gap-2 text-xs sm:text-sm font-semibold overflow-x-auto">
          <button
            onClick={() => setActiveTab("profile")}
            type="button"
            className={`pb-2.5 px-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === "profile"
                ? "border-[#142A3B] text-[#142A3B] font-bold"
                : "border-transparent text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            <IconUser className="w-4 h-4 text-[#285C4D]" />
            <span>Account Details</span>
          </button>
          <button
            onClick={() => setActiveTab("preferences")}
            type="button"
            className={`pb-2.5 px-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === "preferences"
                ? "border-[#142A3B] text-[#142A3B] font-bold"
                : "border-transparent text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            <IconLightbulb className="w-4 h-4 text-[#D97706]" />
            <span>Investment Preferences</span>
          </button>
          <button
            onClick={() => setActiveTab("security")}
            type="button"
            className={`pb-2.5 px-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === "security"
                ? "border-[#142A3B] text-[#142A3B] font-bold"
                : "border-transparent text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            <IconShield className="w-4 h-4 text-[#166534]" />
            <span>Security &amp; Password</span>
          </button>
          <button
            onClick={() => setActiveTab("connected")}
            type="button"
            className={`pb-2.5 px-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === "connected"
                ? "border-[#142A3B] text-[#142A3B] font-bold"
                : "border-transparent text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            <IconLayers className="w-4 h-4 text-[#3B82F6]" />
            <span>Connected Demat</span>
          </button>
          <button
            onClick={() => setActiveTab("account")}
            type="button"
            className={`pb-2.5 px-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === "account"
                ? "border-red-600 text-red-600 font-bold"
                : "border-transparent text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            <IconTrash className="w-4 h-4 text-red-500" />
            <span>Account &amp; Data</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="py-5 min-h-[340px]">
          {/* TAB 1: ACCOUNT DETAILS */}
          {activeTab === "profile" && (
            <div className="space-y-5 animate-fadeIn">
              {profileMessage && (
                <div
                  className={`p-3.5 rounded-xl text-xs flex items-center gap-2 ${
                    profileMessage.type === "success"
                      ? "bg-[#F0FDF4] border border-[#BBF7D0] text-[#166534]"
                      : "bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B]"
                  }`}
                >
                  {profileMessage.type === "success" ? (
                    <IconCheck className="w-4 h-4 text-[#166534]" />
                  ) : (
                    <IconAlertTriangle className="w-4 h-4 text-[#991B1B]" />
                  )}
                  <span>{profileMessage.text}</span>
                </div>
              )}

              {/* Profile Card Header */}
              <div className="p-4 sm:p-5 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-full bg-[#142A3B] text-white flex items-center justify-center font-bold text-base shadow-sm">
                    {nameDisplay.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-[#142A3B] text-base sm:text-lg">
                        {nameDisplay}
                      </h3>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#DCFCE7] text-[#166534] border border-[#BBF7D0]">
                        Active Investor
                      </span>
                    </div>
                    <p className="text-xs text-[#66758A] mt-0.5">
                      Member since {formattedMemberSince}
                    </p>
                  </div>
                </div>

                {!isEditing && (
                  <button
                    onClick={() => setIsEditing(true)}
                    type="button"
                    className="px-3.5 py-1.5 rounded-xl bg-white border border-[#E5E3DA] hover:border-[#142A3B] text-xs font-semibold text-[#142A3B] flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
                  >
                    <IconEdit className="w-3.5 h-3.5 text-[#285C4D]" />
                    <span>Edit Profile</span>
                  </button>
                )}
              </div>

              {/* Profile Details (Read-only vs Edit Form) */}
              {!isEditing ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider flex items-center gap-1">
                      <IconMail className="w-3 h-3 text-[#66758A]" />
                      Registered Email
                    </span>
                    <p className="text-sm font-semibold text-[#142A3B] break-all">{emailDisplay || "Not Provided"}</p>
                    <div className="pt-1">
                      {currentUser?.email_verified ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#166534] bg-[#DCFCE7] px-2.5 py-0.5 rounded-full border border-[#BBF7D0]">
                          <IconCheck className="w-3 h-3" />
                          Verified Email
                        </span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#B45309] bg-[#FEF3C7] px-2.5 py-0.5 rounded-full border border-[#FDE68A]">
                            <IconAlertTriangle className="w-3 h-3 text-[#B45309]" />
                            Unverified Email
                          </span>
                          <button
                            type="button"
                            onClick={() => {
                              setActiveTab("security");
                              setVerifyType("email_verification");
                              setVerifyRecipient(emailDisplay);
                              setVerifyRequested(false);
                              setVerifyStatusMessage(null);
                            }}
                            className="text-[11px] font-semibold text-[#285C4D] hover:underline cursor-pointer"
                          >
                            Verify via OTP →
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider flex items-center gap-1">
                      <IconPhone className="w-3 h-3 text-[#66758A]" />
                      Mobile Number
                    </span>
                    <p className={`text-sm font-semibold ${mobileDisplay ? "text-[#142A3B]" : "text-[#94A3B8] italic"}`}>
                      {mobileDisplay || "Not Provided"}
                    </p>
                    <div className="pt-1">
                      {mobileDisplay ? (
                        currentUser?.mobile_verified ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#166534] bg-[#DCFCE7] px-2.5 py-0.5 rounded-full border border-[#BBF7D0]">
                            <IconCheck className="w-3 h-3" />
                            Verified Mobile
                          </span>
                        ) : (
                          <div className="flex items-center gap-2">
                            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#B45309] bg-[#FEF3C7] px-2.5 py-0.5 rounded-full border border-[#FDE68A]">
                              <IconAlertTriangle className="w-3 h-3 text-[#B45309]" />
                              Unverified Mobile
                            </span>
                            <button
                              type="button"
                              onClick={() => {
                                setActiveTab("security");
                                setVerifyType("mobile_verification");
                                setVerifyRecipient(mobileDisplay);
                                setVerifyRequested(false);
                                setVerifyStatusMessage(null);
                              }}
                              className="text-[11px] font-semibold text-[#285C4D] hover:underline cursor-pointer"
                            >
                              Verify via OTP →
                            </button>
                          </div>
                        )
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#64748B] bg-[#F1F5F9] px-2.5 py-0.5 rounded-full border border-[#E2E8F0]">
                            Not Provided
                          </span>
                          <button
                            type="button"
                            onClick={() => setIsEditing(true)}
                            className="text-[11px] font-semibold text-[#285C4D] hover:underline cursor-pointer"
                          >
                            + Add Mobile
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider">
                      Base Currency &amp; Country
                    </span>
                    <p className="text-sm font-semibold text-[#142A3B]">
                      INR (₹) &bull; India (IN)
                    </p>
                    <p className="text-[11px] text-[#66758A]">NSE &amp; BSE Equity Denomination</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider">
                      Profile Status
                    </span>
                    <p className="text-sm font-semibold text-[#166534] flex items-center gap-1">
                      <IconCheck className="w-4 h-4 text-[#166534]" />
                      100% Completed
                    </p>
                    <p className="text-[11px] text-[#66758A]">SEBI Suitability Profile Active</p>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSaveProfile} className="space-y-4 p-4 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA]">
                  <div className="text-xs font-bold text-[#142A3B] uppercase tracking-wider pb-1 border-b border-[#E5E3DA]">
                    Update Profile Details
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#4A5568] mb-1">
                      Display Name
                    </label>
                    <input
                      type="text"
                      value={displayNameInput}
                      onChange={(e) => setDisplayNameInput(e.target.value)}
                      placeholder="Your Full Name"
                      required
                      className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E3DA] text-sm font-medium text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#4A5568] mb-1">
                      Mobile Number
                    </label>
                    <input
                      type="tel"
                      value={mobileInput}
                      onChange={(e) => setMobileInput(e.target.value)}
                      placeholder="+91 98765 43210"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E3DA] text-sm font-medium text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
                    />
                    <span className="text-[11px] text-[#66758A] mt-1 block">
                      Used for critical portfolio security notifications and two-factor alerts.
                    </span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#4A5568] mb-1">
                      Registered Email
                    </label>
                    <input
                      type="email"
                      value={emailDisplay}
                      disabled
                      className="w-full px-3.5 py-2.5 rounded-xl bg-[#EFECE4] border border-[#E5E3DA] text-sm font-medium text-[#66758A] cursor-not-allowed"
                    />
                    <span className="text-[11px] text-[#66758A] mt-1 block">
                      Primary email address is anchored to your regulatory audit identity.
                    </span>
                  </div>

                  <div className="flex gap-2.5 pt-2">
                    <button
                      type="submit"
                      disabled={savingProfile}
                      className="px-5 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-semibold transition-all cursor-pointer shadow-xs disabled:opacity-50"
                    >
                      {savingProfile ? "Saving..." : "Save Changes"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsEditing(false)}
                      disabled={savingProfile}
                      className="px-4 py-2.5 rounded-xl bg-white hover:bg-[#EFECE4] border border-[#E5E3DA] text-xs font-semibold text-[#4A5568] transition-all cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* TAB 2: INVESTMENT PREFERENCES */}
          {activeTab === "preferences" && (
            <div className="space-y-5 animate-fadeIn">
              <div className="p-4 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-bold text-[#142A3B] uppercase tracking-wider mb-0.5">
                    Fiduciary Suitability Profile
                  </div>
                  <p className="text-xs text-[#66758A]">
                    Preferences calibrated to construct your target risk-adjusted portfolio.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingPreferences(!isEditingPreferences);
                      setPreferencesMessage(null);
                      if (!isEditingPreferences) {
                        setPrefExpInput(activeExp);
                        setPrefKnowledgeInput(activeKnowledge);
                      }
                    }}
                    className="px-3.5 py-2 rounded-xl bg-white hover:bg-[#EFECE4] border border-[#E5E3DA] text-[#142A3B] text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 shadow-xs"
                  >
                    <IconEdit className="w-3.5 h-3.5 text-[#285C4D]" />
                    <span>{isEditingPreferences ? "Cancel" : "Edit Preferences"}</span>
                  </button>
                  {onStartOnboarding && (
                    <button
                      onClick={() => {
                        onClose();
                        onStartOnboarding();
                      }}
                      type="button"
                      className="px-3.5 py-2 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1 cursor-pointer"
                    >
                      <span>Recalibrate</span>
                      <IconArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {preferencesMessage && (
                <div
                  className={`p-3.5 rounded-xl text-xs flex items-center gap-2 ${
                    preferencesMessage.type === "success"
                      ? "bg-[#F0FDF4] border border-[#BBF7D0] text-[#166534]"
                      : "bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B]"
                  }`}
                >
                  {preferencesMessage.type === "success" ? (
                    <IconCheck className="w-4 h-4 text-[#166534]" />
                  ) : (
                    <IconAlertTriangle className="w-4 h-4 text-[#991B1B]" />
                  )}
                  <span>{preferencesMessage.text}</span>
                </div>
              )}

              {isEditingPreferences ? (
                <form
                  onSubmit={handleSavePreferences}
                  className="space-y-4 p-4 sm:p-5 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA]"
                >
                  <div className="text-xs font-bold text-[#142A3B] uppercase tracking-wider pb-1 border-b border-[#E5E3DA]">
                    Adjust Investment Preferences
                  </div>

                  {/* Experience Selector */}
                  <div className="space-y-2">
                    <label className="block text-xs font-semibold text-[#4A5568]">
                      Investment Experience
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                      {[
                        { id: "beginner", label: "Beginner", desc: "New to direct equity investing" },
                        { id: "intermediate", label: "Intermediate", desc: "Mutual funds and select equities" },
                        { id: "experienced", label: "Experienced", desc: "Active direct equity participant" },
                      ].map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => setPrefExpInput(item.id)}
                          className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                            prefExpInput === item.id
                              ? "border-[#142A3B] bg-white text-[#142A3B] font-bold shadow-xs"
                              : "border-[#E5E3DA] bg-[#FAFAF8] text-[#4A5568] hover:border-[#D6D3C8]"
                          }`}
                        >
                          <div className="text-xs font-bold">{item.label}</div>
                          <div className="text-[11px] text-[#66758A] mt-0.5 leading-snug">{item.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Knowledge Selector */}
                  <div className="space-y-2 pt-2">
                    <label className="block text-xs font-semibold text-[#4A5568]">
                      Market Knowledge Level
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                      {[
                        { id: "basic", label: "Basic / Beginner", desc: "Bank deposits, FDs & mutual fund SIPs" },
                        { id: "intermediate", label: "Intermediate", desc: "Balance sheets & diversification" },
                        { id: "advanced", label: "Advanced", desc: "Valuation ratios & market drawdowns" },
                      ].map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => setPrefKnowledgeInput(item.id)}
                          className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                            prefKnowledgeInput === item.id
                              ? "border-[#142A3B] bg-white text-[#142A3B] font-bold shadow-xs"
                              : "border-[#E5E3DA] bg-[#FAFAF8] text-[#4A5568] hover:border-[#D6D3C8]"
                          }`}
                        >
                          <div className="text-xs font-bold">{item.label}</div>
                          <div className="text-[11px] text-[#66758A] mt-0.5 leading-snug">{item.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2.5 pt-3 border-t border-[#E5E3DA]">
                    <button
                      type="submit"
                      disabled={savingPreferences}
                      className="px-5 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-semibold transition-all cursor-pointer shadow-xs disabled:opacity-50"
                    >
                      {savingPreferences ? "Saving..." : "Save Preferences"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsEditingPreferences(false)}
                      disabled={savingPreferences}
                      className="px-4 py-2.5 rounded-xl bg-white hover:bg-[#EFECE4] border border-[#E5E3DA] text-xs font-semibold text-[#4A5568] transition-all cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider">
                      Investment Experience
                    </span>
                    <p className="text-sm font-bold text-[#142A3B] capitalize">
                      {EXPERIENCE_CONFIG[activeExp]?.label || "Beginner"}
                    </p>
                    <p className="text-[11px] text-[#66758A]">
                      {EXPERIENCE_CONFIG[activeExp]?.desc || EXPERIENCE_CONFIG.beginner.desc}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider">
                      Market Knowledge Level
                    </span>
                    <p className="text-sm font-bold text-[#142A3B] capitalize">
                      {KNOWLEDGE_CONFIG[activeKnowledge]?.label || "Basic / Beginner"}
                    </p>
                    <p className="text-[11px] text-[#66758A]">
                      {KNOWLEDGE_CONFIG[activeKnowledge]?.desc || KNOWLEDGE_CONFIG.basic.desc}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider">
                      Active Risk Calibration
                    </span>
                    <div className="flex items-center gap-2 pt-0.5">
                      <span className="text-sm font-bold text-[#285C4D] uppercase">
                        {currentRiskConfig.label}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] font-bold border border-[#C6D8D1]">
                        {currentRiskConfig.vol}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#66758A]">
                      {currentRiskConfig.desc}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1">
                    <span className="text-[11px] font-semibold text-[#66758A] uppercase tracking-wider">
                      Primary Financial Goal
                    </span>
                    <p className="text-sm font-bold text-[#142A3B]">
                      {primaryGoal?.goal_name || "Long-Term Wealth 2030"}
                    </p>
                    <p className="text-[11px] text-[#66758A]">
                      Target Capital: ₹{primaryGoal?.target_amount ? primaryGoal.target_amount.toLocaleString("en-IN") : "2,50,000"} &bull; Horizon: 5+ Years
                    </p>
                  </div>
                </div>
              )}

              {/* Fiduciary Guardrails Summary */}
              <div className="p-4 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] space-y-1.5 text-xs text-[#166534]">
                <div className="font-bold flex items-center gap-1.5">
                  <IconShield className="w-4 h-4 text-[#166534]" />
                  <span>SEBI Regulatory &amp; Fiduciary Guardrails Active</span>
                </div>
                <p className="text-[#14532D]">
                  Every generated portfolio enforces a maximum 25% single-stock cap and 40% sector allocation limit, calculated exclusively with integer whole shares to avoid fractional leakage.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: SECURITY & PASSWORD */}
          {activeTab === "security" && (
            <div className="space-y-6 animate-fadeIn">
              {/* Verification Section */}
              <div className="p-4 sm:p-5 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-3.5">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-[#142A3B] uppercase tracking-wider flex items-center gap-1.5">
                      <IconShield className="w-4 h-4 text-[#166534]" />
                      <span>Contact Verification (OTP)</span>
                    </h3>
                    <p className="text-xs text-[#66758A] mt-0.5">
                      Verify your email or mobile number with a one-time security passkey.
                    </p>
                  </div>
                  {verifyType === "email_verification" ? (
                    currentUser?.email_verified ? (
                      <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#DCFCE7] text-[#166534] border border-[#BBF7D0] inline-flex items-center gap-1">
                        <IconCheck className="w-3 h-3 text-[#166534]" />
                        <span>Email Verified</span>
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A] inline-flex items-center gap-1">
                        <IconAlertTriangle className="w-3 h-3 text-[#B45309]" />
                        <span>Email Unverified</span>
                      </span>
                    )
                  ) : (
                    currentUser?.mobile_verified ? (
                      <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#DCFCE7] text-[#166534] border border-[#BBF7D0] inline-flex items-center gap-1">
                        <IconCheck className="w-3 h-3 text-[#166534]" />
                        <span>Mobile Verified</span>
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A] inline-flex items-center gap-1">
                        <IconAlertTriangle className="w-3 h-3 text-[#B45309]" />
                        <span>Mobile Unverified</span>
                      </span>
                    )
                  )}
                </div>

                <div className="flex gap-4 text-xs font-medium text-[#4A5568]">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="verifyType"
                      checked={verifyType === "email_verification"}
                      onChange={() => {
                        setVerifyType("email_verification");
                        setVerifyRecipient(currentUser?.email || emailDisplay || "");
                        setVerifyRequested(false);
                        setVerifyStatusMessage(null);
                        setVerifyDemoCode(null);
                        setVerifyCodeInput("");
                      }}
                    />
                    <span>Email OTP</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="verifyType"
                      checked={verifyType === "mobile_verification"}
                      onChange={() => {
                        setVerifyType("mobile_verification");
                        setVerifyRecipient(currentUser?.mobile_number || mobileInput || "");
                        setVerifyRequested(false);
                        setVerifyStatusMessage(null);
                        setVerifyDemoCode(null);
                        setVerifyCodeInput("");
                      }}
                    />
                    <span>Mobile SMS OTP</span>
                  </label>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={verifyRecipient}
                    onChange={(e) => setVerifyRecipient(e.target.value)}
                    placeholder={
                      verifyType === "email_verification"
                        ? (emailDisplay || "Enter email address")
                        : (mobileDisplay || "Enter mobile phone number e.g. +91 98765 43210")
                    }
                    className="flex-1 px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E3DA] text-xs font-medium text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
                  />
                  <button
                    onClick={handleRequestVerification}
                    disabled={isVerifying}
                    type="button"
                    className="px-4 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-semibold transition-all disabled:opacity-50 cursor-pointer shadow-xs whitespace-nowrap"
                  >
                    {isVerifying ? "Sending..." : verifyType === "email_verification" ? "Send Email OTP" : "Send Mobile SMS OTP"}
                  </button>
                </div>

                {verifyDemoCode && (
                  <div className="p-2.5 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] text-xs text-[#1E40AF]">
                    <strong>Development OTP Preview:</strong> Use code <code className="font-mono bg-white px-1.5 py-0.5 rounded font-bold">{verifyDemoCode}</code>
                  </div>
                )}

                {verifyRequested && (
                  <div className="space-y-2 pt-2 border-t border-[#E5E3DA]">
                    <label className="block text-xs font-medium text-[#4A5568]">
                      Enter 6-Digit Verification Code
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        maxLength={6}
                        value={verifyCodeInput}
                        onChange={(e) => setVerifyCodeInput(e.target.value)}
                        placeholder="123456"
                        className="w-36 px-3 py-2 rounded-xl bg-white border border-[#E5E3DA] text-center font-mono font-bold tracking-widest text-sm text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
                      />
                      <button
                        onClick={handleVerifyCode}
                        disabled={isVerifying || verifyCodeInput.length < 4}
                        type="button"
                        className="px-5 py-2 rounded-xl bg-[#166534] hover:bg-[#14532D] text-white text-xs font-semibold transition-all disabled:opacity-50 cursor-pointer shadow-xs"
                      >
                        {isVerifying ? "Verifying..." : "Confirm Code"}
                      </button>
                    </div>
                  </div>
                )}

                {verifyStatusMessage && (
                  <div
                    className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                      verifyStatusMessage.type === "success"
                        ? "bg-[#F0FDF4] border border-[#BBF7D0] text-[#166534]"
                        : "bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B]"
                    }`}
                  >
                    {verifyStatusMessage.type === "success" ? (
                      <IconCheck className="w-4 h-4 text-[#166534]" />
                    ) : (
                      <IconAlertTriangle className="w-4 h-4 text-[#991B1B]" />
                    )}
                    <span>{verifyStatusMessage.text}</span>
                  </div>
                )}
              </div>

              {/* Change Password Section */}
              <form onSubmit={handleChangePassword} className="p-4 sm:p-5 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-3.5">
                <div>
                  <h3 className="text-xs font-bold text-[#142A3B] uppercase tracking-wider flex items-center gap-1.5">
                    <IconLock className="w-4 h-4 text-[#142A3B]" />
                    <span>Change Password</span>
                  </h3>
                  <p className="text-xs text-[#66758A] mt-0.5">
                    Keep your account secure by choosing a unique, strong password.
                  </p>
                </div>

                <div className="space-y-3 pt-1">
                  <div>
                    <label className="block text-xs font-medium text-[#4A5568] mb-1">
                      Current Password (Optional for demo accounts)
                    </label>
                    <input
                      type="password"
                      value={currentPasswordInput}
                      onChange={(e) => setCurrentPasswordInput(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#E5E3DA] text-xs text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div>
                      <label className="block text-xs font-medium text-[#4A5568] mb-1">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={newPasswordInput}
                        onChange={(e) => setNewPasswordInput(e.target.value)}
                        placeholder="Min 6 characters"
                        required
                        className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#E5E3DA] text-xs text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[#4A5568] mb-1">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={confirmPasswordInput}
                        onChange={(e) => setConfirmPasswordInput(e.target.value)}
                        placeholder="Re-enter password"
                        required
                        className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#E5E3DA] text-xs text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isChangingPassword || !newPasswordInput}
                    className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-semibold transition-all disabled:opacity-50 cursor-pointer shadow-xs"
                  >
                    {isChangingPassword ? "Updating Password..." : "Update Password"}
                  </button>

                  {passwordStatusMessage && (
                    <div
                      className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                        passwordStatusMessage.type === "success"
                          ? "bg-[#F0FDF4] border border-[#BBF7D0] text-[#166534]"
                          : "bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B]"
                      }`}
                    >
                      {passwordStatusMessage.type === "success" ? (
                        <IconCheck className="w-4 h-4 text-[#166534]" />
                      ) : (
                        <IconAlertTriangle className="w-4 h-4 text-[#991B1B]" />
                      )}
                      <span>{passwordStatusMessage.text}</span>
                    </div>
                  )}
                </div>
              </form>

              {/* Active Session & Sign Out */}
              <div className="p-4 rounded-xl bg-white border border-[#E5E3DA] flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-[#142A3B]">Active Session</span>
                  <p className="text-xs text-[#66758A]">
                    Signed in securely via cryptographic session token.
                  </p>
                </div>
                <button
                  onClick={handleSignOut}
                  type="button"
                  className="px-4 py-2 rounded-xl border border-[#FECACA] bg-[#FEF2F2] hover:bg-[#FEE2E2] text-xs font-bold text-[#B91C1C] transition-colors cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            </div>
          )}

          {/* TAB 4: CONNECTED DEMAT / BROKERS */}
          {activeTab === "connected" && (
            <div className="space-y-4 animate-fadeIn">
              <div className="p-4 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                <div className="text-xs font-bold text-[#142A3B] uppercase tracking-wider">
                  Non-Custodial Architecture
                </div>
                <p className="text-xs text-[#66758A]">
                  Lucid does not hold user funds, custody equity shares, or store brokerage trading credentials. All trade allocations are calculated with mathematical rigor and executed directly by you in your broker app.
                </p>
              </div>

              <div className="space-y-2.5">
                <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] flex items-center justify-between">
                  <div>
                    <strong className="text-xs text-[#142A3B] block">Zerodha Kite</strong>
                    <span className="text-[11px] text-[#66758A]">Manual / Non-Custodial Order Dispatch</span>
                  </div>
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                    Self-Directed
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] flex items-center justify-between">
                  <div>
                    <strong className="text-xs text-[#142A3B] block">Groww Demat</strong>
                    <span className="text-[11px] text-[#66758A]">Integer Share Basket Import</span>
                  </div>
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                    Self-Directed
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] flex items-center justify-between">
                  <div>
                    <strong className="text-xs text-[#142A3B] block">Upstox &amp; Angel One</strong>
                    <span className="text-[11px] text-[#66758A]">NSE / BSE Whole Share Order Compatibility</span>
                  </div>
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                    Self-Directed
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] text-xs text-[#1E40AF]">
                <strong>Fiduciary Safety Note:</strong> When you execute recommendations, always review final market prices and transaction costs. Lucid will never automatically place live financial orders without your manual review and approval.
              </div>
            </div>
          )}

          {/* TAB 5: ACCOUNT & DATA MANAGEMENT */}
          {activeTab === "account" && (
            <div className="space-y-6 animate-fadeIn">
              {/* Introduction */}
              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <h4 className="text-sm font-bold text-[#142A3B] mb-1">
                  User Data Management &amp; Privacy Rights
                </h4>
                <p className="text-xs text-[#66758A] leading-relaxed">
                  Lucid operates with non-custodial fiduciary transparency. You maintain full ownership and control over your personal data, saved portfolios, and account lifecycle under SEBI advisory norms and GDPR standards.
                </p>
              </div>

              {/* Section 1: Pre-Deletion Data Portability / Export */}
              <div className="p-5 rounded-xl bg-white border border-[#E5E3DA] space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-bold text-[#142A3B] flex items-center gap-2">
                      <IconDownloadCloud className="w-4 h-4 text-[#285C4D]" />
                      <span>Download Your Saved Data (JSON)</span>
                    </h4>
                    <p className="text-xs text-[#66758A] mt-1 leading-relaxed">
                      Download a structured archive containing your profile, preferences, financial goals, risk assessments, and portfolio holdings before initiating account deletion.
                    </p>
                  </div>
                </div>

                {exportSuccessMessage && (
                  <div className="p-3 rounded-lg bg-green-50 border border-green-200 text-green-800 text-xs flex items-center gap-2">
                    <IconCheck className="w-4 h-4 text-green-600 shrink-0" />
                    <span>{exportSuccessMessage}</span>
                  </div>
                )}
                {exportErrorMessage && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
                    <IconAlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                    <span>{exportErrorMessage}</span>
                  </div>
                )}

                <button
                  onClick={handleExportData}
                  disabled={isExportingData}
                  type="button"
                  className="px-4 py-2 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] disabled:opacity-50 text-white text-xs font-bold flex items-center gap-2 transition-colors cursor-pointer shadow-xs"
                >
                  {isExportingData ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                      <span>Exporting Data...</span>
                    </>
                  ) : (
                    <>
                      <IconDownloadCloud className="w-3.5 h-3.5" />
                      <span>Download My Data (JSON)</span>
                    </>
                  )}
                </button>
              </div>

              {/* Section 2: Portfolio Deletion & Management */}
              <div className="p-5 rounded-xl bg-white border border-[#E5E3DA] space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-bold text-[#142A3B] flex items-center gap-2">
                      <IconTrash className="w-4 h-4 text-[#B45309]" />
                      <span>Manage &amp; Delete Portfolios</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-[#F7F6F1] text-[#4A5568] border border-[#E5E3DA] font-semibold">
                        {portfoliosList.length} {portfoliosList.length === 1 ? "portfolio" : "portfolios"}
                      </span>
                    </h4>
                    <p className="text-xs text-[#66758A] mt-1 leading-relaxed">
                      Select specific portfolios to delete, batch remove multiple allocations, or wipe all portfolios without deleting your account or financial goals.
                    </p>
                  </div>

                  {portfoliosList.length > 0 && (
                    <div className="flex items-center gap-2 shrink-0 flex-wrap">
                      {selectedPortfolioIds.length > 0 && (
                        <button
                          onClick={handleRequestDeleteSelected}
                          type="button"
                          className="px-3 py-1.5 rounded-lg border border-red-300 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
                        >
                          <IconTrash className="w-3.5 h-3.5" />
                          <span>Delete Selected ({selectedPortfolioIds.length})</span>
                        </button>
                      )}
                      <button
                        onClick={handleRequestDeleteAll}
                        type="button"
                        className="px-3 py-1.5 rounded-lg border border-[#E5E3DA] hover:border-red-200 bg-white hover:bg-red-50 text-red-600 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                      >
                        <IconTrash className="w-3.5 h-3.5" />
                        <span>Delete All Portfolios</span>
                      </button>
                    </div>
                  )}
                </div>

                {portfolioNotice && (
                  <div
                    className={`p-3 rounded-xl text-xs flex items-center justify-between gap-2 animate-fadeIn ${
                      portfolioNotice.type === "success"
                        ? "bg-green-50 border border-green-200 text-green-800"
                        : "bg-red-50 border border-red-200 text-red-800"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {portfolioNotice.type === "success" ? (
                        <IconCheck className="w-4 h-4 text-green-600 shrink-0" />
                      ) : (
                        <IconAlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                      )}
                      <span>{portfolioNotice.text}</span>
                    </div>
                    <button
                      onClick={() => setPortfolioNotice(null)}
                      type="button"
                      className="p-1 hover:bg-black/5 rounded cursor-pointer"
                    >
                      <IconX className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {portfoliosList.length === 0 ? (
                  <div className="p-6 text-center rounded-xl bg-[#FDFBF7] border border-dashed border-[#E5E3DA] space-y-1.5">
                    <p className="text-xs font-semibold text-[#142A3B]">No portfolios currently saved</p>
                    <p className="text-[11px] text-[#66758A]">
                      You have no active or historical portfolios. Build a new portfolio to get personalized recommendations.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {/* Select All Toolbar */}
                    <div className="flex items-center justify-between text-xs px-2.5 py-1.5 bg-[#FDFBF7] border border-[#E5E3DA] rounded-lg text-[#66758A]">
                      <label className="flex items-center gap-2 cursor-pointer font-medium select-none">
                        <input
                          type="checkbox"
                          checked={portfoliosList.length > 0 && selectedPortfolioIds.length === portfoliosList.length}
                          onChange={handleToggleSelectAll}
                          className="w-3.5 h-3.5 rounded border-[#E5E3DA] text-[#285C4D] focus:ring-0 cursor-pointer"
                        />
                        <span>
                          {selectedPortfolioIds.length === portfoliosList.length ? "Deselect All" : "Select All"}
                        </span>
                      </label>
                      <span>
                        {selectedPortfolioIds.length} of {portfoliosList.length} selected
                      </span>
                    </div>

                    {/* Scrollable list of portfolios */}
                    <div className="max-h-64 overflow-y-auto space-y-2 pr-1">
                      {portfoliosList.map((p) => {
                        const isSelected = selectedPortfolioIds.includes(p.portfolio_id);
                        const isActive = activePortfolio?.portfolio_id === p.portfolio_id;
                        const pName = p.portfolio_name || `Portfolio v#${p.latest_version?.version_number || 1}`;
                        const capital = p.latest_version?.investment_amount
                          ? `₹${Number(p.latest_version.investment_amount).toLocaleString("en-IN")}`
                          : "₹2,50,000";
                        const risk = p.latest_version?.risk_category?.replace("_", " ") || "Moderate";
                        const holdings = p.latest_version?.holdings?.length ?? 0;
                        const dateStr = p.created_at
                          ? new Date(p.created_at).toLocaleDateString("en-IN", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })
                          : "Recently";

                        return (
                          <div
                            key={p.portfolio_id}
                            className={`p-3 rounded-xl border transition-all flex items-center justify-between gap-3 text-xs ${
                              isSelected
                                ? "bg-red-50/40 border-red-300 shadow-2xs"
                                : "bg-white border-[#E5E3DA] hover:border-[#CBD5E1]"
                            }`}
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => handleToggleSelectPortfolio(p.portfolio_id)}
                                aria-label={`Select ${pName}`}
                                className="w-4 h-4 rounded border-[#E5E3DA] text-[#285C4D] focus:ring-0 cursor-pointer shrink-0"
                              />
                              <div className="min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="font-bold text-[#142A3B] truncate">{pName}</span>
                                  {isActive && (
                                    <span className="px-2 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1] text-[10px] font-bold">
                                      Active Portfolio
                                    </span>
                                  )}
                                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#F7F6F1] border border-[#E5E3DA] text-[#66758A] uppercase font-semibold">
                                    {risk}
                                  </span>
                                </div>
                                <div className="text-[11px] text-[#66758A] flex items-center gap-2 mt-0.5 flex-wrap">
                                  <span>{capital}</span>
                                  <span>•</span>
                                  <span>{holdings} stocks</span>
                                  <span>•</span>
                                  <span>Created {dateStr}</span>
                                </div>
                              </div>
                            </div>

                            <button
                              onClick={() => handleRequestDeleteSingle(p)}
                              type="button"
                              aria-label={`Delete portfolio ${pName}`}
                              className="px-2.5 py-1.5 rounded-lg border border-[#E5E3DA] hover:border-red-300 bg-white hover:bg-red-50 text-red-600 font-semibold text-xs flex items-center gap-1.5 transition-colors shrink-0 cursor-pointer"
                            >
                              <IconTrash className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">Delete</span>
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Section 3: Permanent Account Deletion (Danger Zone) */}
              <div className="p-5 rounded-xl bg-red-50/40 border border-red-200 space-y-4">
                <div className="flex items-center gap-2.5 text-red-700">
                  <IconAlertCircle className="w-5 h-5 shrink-0 text-red-600" />
                  <h4 className="text-sm font-bold">Permanently Delete Account</h4>
                </div>

                <p className="text-xs text-[#4A5568] leading-relaxed">
                  Deleting your Lucid account will remove your access to the application and initiate the permanent deletion or anonymization of your associated personal information and saved investment data, subject to applicable legal and retention requirements. <strong>This action is irreversible.</strong>
                </p>

                <div className="p-3 rounded-lg bg-white border border-red-100 text-xs text-[#66758A] space-y-1">
                  <div className="font-semibold text-red-800">Records permanently removed:</div>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px] text-[#4A5568]">
                    <li>Account profile, email, and verified mobile records</li>
                    <li>All saved portfolios, holdings, version history, and order slips</li>
                    <li>Financial goals and SEBI risk assessment questionnaire answers</li>
                    <li>AI conversational copilot memory cache and session history</li>
                    <li>Active login sessions and cryptographic JWT tokens</li>
                  </ul>
                </div>

                {accountDeleteSuccess && (
                  <div className="p-3.5 rounded-xl bg-green-50 border border-green-200 text-green-800 text-xs font-semibold flex items-center gap-2 animate-fadeIn">
                    <IconCheck className="w-4 h-4 text-green-600 shrink-0" />
                    <span>Your Lucid account and records have been permanently deleted. Logging out...</span>
                  </div>
                )}

                {accountDeleteError && (
                  <div className="p-3 rounded-xl bg-red-100 border border-red-300 text-red-800 text-xs flex items-center gap-2">
                    <IconAlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                    <span>{accountDeleteError}</span>
                  </div>
                )}

                {!accountDeleteSuccess && (
                  <div className="space-y-3 pt-1">
                    {/* Password verification input (if password account) */}
                    <div>
                      <label className="block text-xs font-semibold text-[#142A3B] mb-1">
                        Current Password (if set)
                      </label>
                      <input
                        type="password"
                        placeholder="Enter account password"
                        value={accountDeletePassword}
                        onChange={(e) => setAccountDeletePassword(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-[#E5E3DA] bg-white focus:outline-hidden focus:border-red-500"
                      />
                    </div>

                    {/* Confirmation phrase input */}
                    <div>
                      <label className="block text-xs font-semibold text-[#142A3B] mb-1">
                        Type <span className="font-mono text-red-600 bg-red-100 px-1 py-0.5 rounded">DELETE MY ACCOUNT</span> to confirm
                      </label>
                      <input
                        type="text"
                        placeholder="DELETE MY ACCOUNT"
                        value={accountDeletePhrase}
                        onChange={(e) => setAccountDeletePhrase(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-[#E5E3DA] bg-white font-mono focus:outline-hidden focus:border-red-500"
                      />
                    </div>

                    <button
                      onClick={handlePermanentAccountDeletion}
                      disabled={isDeletingAccount || accountDeletePhrase.trim().toUpperCase() !== "DELETE MY ACCOUNT"}
                      type="button"
                      className="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-xs"
                    >
                      {isDeletingAccount ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                          <span>Permanently Deleting Account...</span>
                        </>
                      ) : (
                        <>
                          <IconTrash className="w-3.5 h-3.5" />
                          <span>Permanently Delete My Account</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Delete Portfolio Confirmation Modal inside Profile */}
        <DeletePortfolioModal
          isOpen={isDeletePortfolioModalOpen}
          onClose={() => setIsDeletePortfolioModalOpen(false)}
          portfolios={deleteTargets}
          isDeleteAll={isDeleteAllMode}
          onDeleted={handlePortfoliosDeleted}
        />

        {/* Footer */}
        <div className="pt-4 border-t border-[#E5E3DA] flex items-center justify-between">
          <span className="text-[11px] text-[#66758A]">
            Lucid Portfolio Engine &bull; Non-Custodial Wealth Analytics
          </span>
          <button
            onClick={onClose}
            type="button"
            className="px-5 py-2.5 rounded-xl bg-[#F7F6F1] hover:bg-[#EFECE4] border border-[#E5E3DA] text-[#142A3B] text-xs font-semibold transition-all cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
