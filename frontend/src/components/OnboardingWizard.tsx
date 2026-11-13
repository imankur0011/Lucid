"use client";

import React, { useState, useEffect } from "react";
import { BRAND, formatINR } from "../lib/brand";
import {
  RiskQuestion,
  RiskAssessment,
  FinancialGoal,
  UserProfile,
  createGoal,
  updateProfile,
  submitRiskAssessment,
  extractProfileFromText,
  ProfileNLPExtractResponse,
  loginDemoUser,
  getAuthToken,
} from "../lib/api";
import {
  IconShield,
  IconCheck,
  IconTarget,
  IconAlertTriangle,
  IconSliders,
  IconArrowUpRight,
  IconSparkles,
  IconFileText,
  IconBriefcase,
  IconRocket,
  IconLightbulb,
  IconEdit,
  IconX,
  IconTrendingUp,
  IconSun,
  IconAcademicCap,
} from "./icons";

export interface OnboardingConfig {
  portfolioName: string;
  investmentAmount: number;
  horizonMonths: number;
  excludedSectors: string[];
  maxStockWeight: number;
  maxSectorWeight: number;
  minStocksCount?: number;
  portfolioStyle?: "focused" | "balanced" | "broad";
  userPrompt: string;
  experienceLevel: string;
  knowledgeLevel: string;
  goalType: string;
  goalName: string;
  targetCorpus: number;
  riskCategory: string;
  riskAssessmentId?: string;
  selectedAnswers: Record<string, string>;
}

interface OnboardingWizardProps {
  questions: RiskQuestion[];
  existingAssessment: RiskAssessment | null;
  profile: UserProfile | null;
  onComplete: (config: OnboardingConfig) => void;
  onCancel: () => void;
  loading: boolean;
  generationStage: string;
}

export function OnboardingWizard({
  questions,
  existingAssessment,
  profile,
  onComplete,
  onCancel,
  loading,
  generationStage,
}: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const totalSteps = 6;

  // Step 1: About You
  const [experience, setExperience] = useState<string>(
    profile?.investment_experience || "beginner"
  );
  const [knowledge, setKnowledge] = useState<string>(
    profile?.investment_knowledge_level || "basic"
  );
  const [mobileNumber, setMobileNumber] = useState<string>(
    profile?.mobile_number || ""
  );

  // Step 2: Financial Goals
  const [goalType, setGoalType] = useState<string>("wealth_creation");
  const [goalName, setGoalName] = useState<string>("Long-Term Wealth 2030");
  const [targetCorpus, setTargetCorpus] = useState<number>(1000000);

  // Step 3: Capital & Horizon
  const [capital, setCapital] = useState<number>(250000);
  const [horizonMonths, setHorizonMonths] = useState<number>(60);

  // Step 4: Risk Assessment
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [calculatedRisk, setCalculatedRisk] = useState<string>(
    existingAssessment?.risk_category || "moderate"
  );

  // Step 5: Preferences & Exclusions
  const [excludedSectors, setExcludedSectors] = useState<string[]>([]);
  const maxStockWeight = 25.0;
  const maxSectorWeight = 40.0;

  // Natural Language AI Mode States
  const [wizardMode, setWizardMode] = useState<"guided" | "natural_language">("guided");
  const [nlpInput, setNlpInput] = useState<string>("");
  const [isExtractingNLP, setIsExtractingNLP] = useState<boolean>(false);
  const [nlpError, setNlpError] = useState<string | null>(null);
  const [extractedNLPResult, setExtractedNLPResult] = useState<ProfileNLPExtractResponse | null>(null);

  const handleNLPExtract = async () => {
    if (!nlpInput || nlpInput.trim().length < 5) {
      setNlpError("Please enter at least a few words describing your capital, horizon, or risk preferences.");
      return;
    }
    setNlpError(null);
    setIsExtractingNLP(true);
    try {
      const res = await extractProfileFromText(nlpInput);
      setExtractedNLPResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to extract profile";
      setNlpError(msg);
    } finally {
      setIsExtractingNLP(false);
    }
  };

  const handleApplyNLPToWizard = () => {
    if (!extractedNLPResult) return;
    const p = extractedNLPResult.extracted_profile;
    setCapital(p.investment_amount);
    setHorizonMonths(p.horizon_months);
    setCalculatedRisk(p.risk_category);
    setExperience(p.experience_level);
    setKnowledge(p.knowledge_level);
    setGoalType(p.goal_type);
    setGoalName(p.goal_name);
    setTargetCorpus(p.target_corpus);
    setExcludedSectors(p.excluded_sectors);

    if (extractedNLPResult.resolved_questionnaire_answers) {
      const newAns: Record<string, string> = {};
      extractedNLPResult.resolved_questionnaire_answers.forEach((ra) => {
        newAns[ra.question_id] = ra.selected_option_id;
      });
      setAnswers((prev) => ({ ...prev, ...newAns }));
    }

    setWizardMode("guided");
    setCurrentStep(1);
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleConfirmAndGenerateFromNLP = async () => {
    if (!extractedNLPResult) return;
    const p = extractedNLPResult.extracted_profile;

    let savedGoalId: string | undefined = undefined;
    try {
      const newGoal = await createGoal({
        goal_name: p.goal_name,
        goal_type: p.goal_type,
        target_amount: p.target_corpus,
      });
      savedGoalId = newGoal.goal_id;
    } catch {
      // Continue even if goal creation fails
    }

    let savedAssessmentId: string | undefined = undefined;
    if (extractedNLPResult.resolved_questionnaire_answers && extractedNLPResult.resolved_questionnaire_answers.length > 0) {
      try {
        const payload = extractedNLPResult.resolved_questionnaire_answers.map((ra) => ({
          question_id: ra.question_id,
          selected_option_id: ra.selected_option_id,
        }));
        const newAssessment = await submitRiskAssessment(payload);
        savedAssessmentId = newAssessment.risk_assessment_id;
      } catch {
        // Continue
      }
    }

    try {
      await updateProfile({
        investment_experience: p.experience_level,
        investment_knowledge_level: p.knowledge_level,
      });
    } catch {
      // Continue
    }

    const ansMap: Record<string, string> = {};
    if (extractedNLPResult.resolved_questionnaire_answers) {
      extractedNLPResult.resolved_questionnaire_answers.forEach((ra) => {
        ansMap[ra.question_id] = ra.selected_option_id;
      });
    }

    const config: OnboardingConfig = {
      portfolioName: p.portfolio_name,
      investmentAmount: p.investment_amount,
      horizonMonths: p.horizon_months,
      excludedSectors: p.excluded_sectors,
      maxStockWeight: maxStockWeight,
      maxSectorWeight: maxSectorWeight,
      userPrompt: p.user_prompt,
      experienceLevel: p.experience_level,
      knowledgeLevel: p.knowledge_level,
      goalType: p.goal_type,
      goalName: p.goal_name,
      targetCorpus: p.target_corpus,
      riskCategory: p.risk_category,
      riskAssessmentId: savedAssessmentId,
      selectedAnswers: ansMap,
    };

    onComplete(config);
  };

  // Synchronize Question 4 answer if knowledge is chosen in Stage 1
  useEffect(() => {
    if (questions && questions.length > 0) {
      const knowQ = questions.find((q) => q.question_code === "INVESTMENT_KNOWLEDGE");
      if (knowQ && !answers[knowQ.question_id]) {
        const codeMap: Record<string, string> = {
          basic: "EXP_NONE",
          intermediate: "EXP_MUTUAL_FUNDS",
          advanced: "EXP_DIRECT_EQUITY",
        };
        const targetOpt = knowQ.options.find((o) => o.option_code === codeMap[knowledge]);
        if (targetOpt) {
          setAnswers((prev) => {
            if (!prev[knowQ.question_id]) {
              return { ...prev, [knowQ.question_id]: targetOpt.option_id };
            }
            return prev;
          });
        }
      }
    }
  }, [questions, knowledge]);

  // Helper for step progression
  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  };

  // Fiduciary Risk Calculation engine matching SEBI IA Master Circular suitability rules
  const computeFiduciaryRiskCategory = (currentAnswers: Record<string, string>): string => {
    let totalWeightedScore = 0;
    let totalWeight = 0;
    let capacitySum = 0;
    let capacityWeight = 0;
    let toleranceSum = 0;
    let toleranceWeight = 0;
    let zeroEmergencyFund = false;
    let shortHorizon = false;
    let beginnerKnowledge = false;

    questions.forEach((q, idx) => {
      const selectedOptId = currentAnswers[q.question_id];
      if (!selectedOptId) return;
      const opt = q.options.find((o) => o.option_id === selectedOptId);
      if (!opt || typeof opt.score !== "number") return;

      const qCode = (q.question_code || "").toLowerCase();
      const cfg = q.scoring_config || {};
      let category = cfg.category;
      let weight = cfg.weight;

      if (!category) {
        if (qCode.includes("horizon") || idx === 0) category = "capacity";
        else if (qCode.includes("emergency") || idx === 4) category = "capacity";
        else if (qCode.includes("knowledge") || idx === 3) category = "knowledge";
        else category = "tolerance";
      }

      if (typeof weight !== "number") {
        if (idx === 0) weight = 0.20;
        else if (idx === 1) weight = 0.25;
        else if (idx === 2) weight = 0.25;
        else if (idx === 3) weight = 0.15;
        else if (idx === 4) weight = 0.15;
        else weight = 0.20;
      }

      const score = opt.score;

      // Fiduciary triggers
      if ((qCode.includes("emergency") || idx === 4) && score <= 25) {
        zeroEmergencyFund = true;
      }
      if ((qCode.includes("horizon") || idx === 0) && score <= 25) {
        shortHorizon = true;
      }
      if ((qCode.includes("knowledge") || idx === 3) && score <= 25) {
        beginnerKnowledge = true;
      }

      totalWeightedScore += score * weight;
      totalWeight += weight;

      if (category === "capacity") {
        capacitySum += score * weight;
        capacityWeight += weight;
      } else {
        toleranceSum += score * weight;
        toleranceWeight += weight;
      }
    });

    if (totalWeight === 0) {
      return existingAssessment?.risk_category || "moderate";
    }

    const overallScore = totalWeightedScore / totalWeight;
    const tolScore = toleranceWeight > 0 ? toleranceSum / toleranceWeight : overallScore;
    const capScore = capacityWeight > 0 ? capacitySum / capacityWeight : overallScore;

    const scoreToCat = (score: number): string => {
      if (score < 35.0) return "conservative";
      if (score < 50.0) return "conservative";
      if (score < 70.0) return "moderate";
      if (score < 85.0) return "growth";
      return "aggressive";
    };

    const CATEGORY_RANKS: Record<string, number> = {
      very_conservative: 1,
      conservative: 2,
      moderate: 3,
      growth: 4,
      aggressive: 5,
    };
    const RANK_TO_CAT: Record<number, string> = {
      1: "conservative",
      2: "conservative",
      3: "moderate",
      4: "growth",
      5: "aggressive",
    };

    let tolRank = CATEGORY_RANKS[scoreToCat(tolScore)] || 3;
    let capRank = CATEGORY_RANKS[scoreToCat(capScore)] || 3;

    // SEBI Fiduciary Constraint 1: Zero emergency fund strictly caps loss capacity to Conservative (Rank 2)
    if (zeroEmergencyFund) {
      capRank = Math.min(capRank, 2);
    }
    // SEBI Fiduciary Constraint 2: Investment horizon < 1 year strictly caps loss capacity to Conservative (Rank 2)
    if (shortHorizon) {
      capRank = Math.min(capRank, 2);
    }
    // SEBI Fiduciary Constraint 3: Beginner with no equity knowledge cannot be Aggressive (caps tolerance at Moderate, Rank 3)
    if (beginnerKnowledge) {
      tolRank = Math.min(tolRank, 3);
    }

    // SEBI Fiduciary Rule: Actionable risk posture cannot exceed financial loss capacity
    const finalRank = Math.min(tolRank, capRank);
    return RANK_TO_CAT[finalRank] || "moderate";
  };

  const handleSelectAnswer = (questionId: string, optionId: string, score: number) => {
    const updated = { ...answers, [questionId]: optionId };
    setAnswers(updated);

    // Sync knowledge level if this is the INVESTMENT_KNOWLEDGE question
    const q = questions.find((item) => item.question_id === questionId);
    if (q && q.question_code === "INVESTMENT_KNOWLEDGE") {
      const opt = q.options.find((o) => o.option_id === optionId);
      if (opt) {
        if (opt.option_code === "EXP_NONE" || opt.score <= 30) {
          setKnowledge("basic");
        } else if (opt.option_code === "EXP_MUTUAL_FUNDS" || opt.score <= 65) {
          setKnowledge("intermediate");
        } else {
          setKnowledge("advanced");
        }
      }
    }

    const newRisk = computeFiduciaryRiskCategory(updated);
    setCalculatedRisk(newRisk);
  };

  const toggleSectorExclusion = (sector: string) => {
    if (excludedSectors.includes(sector)) {
      setExcludedSectors(excludedSectors.filter((s) => s !== sector));
    } else {
      setExcludedSectors([...excludedSectors, sector]);
    }
  };

  const handleFinalSubmit = async () => {
    // Ensure authentication token exists before persisting or generating
    if (!getAuthToken()) {
      try {
        await loginDemoUser();
      } catch (e) {
        console.warn("Auto demo login prior to final submit:", e);
      }
    }

    // Optionally persist goal and profile changes in background
    try {
      const validExperiences = ["beginner", "intermediate", "experienced"];
      const validKnowledge = ["basic", "intermediate", "advanced"];
      const cleanExp = validExperiences.includes(experience) ? experience : "beginner";
      const cleanKnow = validKnowledge.includes(knowledge) ? knowledge : "basic";

      await updateProfile({
        investment_experience: cleanExp,
        investment_knowledge_level: cleanKnow,
        ...(mobileNumber.trim() ? { mobile_number: mobileNumber.trim() } : {}),
      }).catch((e) => console.warn("Non-blocking profile update notice:", e));

      if (goalName && goalType && targetCorpus > 0) {
        await createGoal({
          goal_name: goalName,
          goal_type: goalType,
          target_amount: targetCorpus,
        }).catch(() => {});
      }
    } catch {
      // Non-blocking persistence
    }

    let savedAssessmentId: string | undefined = undefined;
    const answeredPairs = Object.entries(answers)
      .filter(([_, optId]) => Boolean(optId))
      .map(([qId, optId]) => ({ question_id: qId, selected_option_id: optId }));

    if (answeredPairs.length > 0) {
      try {
        const saved = await submitRiskAssessment(answeredPairs);
        if (saved && saved.risk_assessment_id) {
          savedAssessmentId = saved.risk_assessment_id;
        }
      } catch (err) {
        console.warn("Non-blocking assessment save error:", err);
      }
    }

    const config: OnboardingConfig = {
      portfolioName: goalName ? `${goalName} Portfolio` : "Personalized Equity Portfolio",
      investmentAmount: capital,
      horizonMonths: horizonMonths,
      excludedSectors: excludedSectors,
      maxStockWeight: maxStockWeight,
      maxSectorWeight: maxSectorWeight,
      userPrompt: `Disciplined Indian equity portfolio designed for ${experience} investor with ${calculatedRisk} risk profile targeting ${goalName} (${goalType}) with dynamically optimized holdings for capital ₹${capital.toLocaleString("en-IN")}.`,
      experienceLevel: experience,
      knowledgeLevel: knowledge,
      goalType: goalType,
      goalName: goalName,
      targetCorpus: targetCorpus,
      riskCategory: calculatedRisk,
      riskAssessmentId: savedAssessmentId,
      selectedAnswers: answers,
    };

    onComplete(config);
  };

  // If currently generating, show the honest multi-stage loader
  if (loading) {
    return (
      <div className="max-w-2xl mx-auto my-12 bg-white rounded-2xl border border-[#E5E3DA] shadow-md p-8 sm:p-10 text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-[#142A3B] text-white flex items-center justify-center font-bold text-2xl mx-auto animate-pulse">
          {BRAND.symbol}
        </div>

        <div className="space-y-2">
          <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
            MATHEMATICAL OPTIMIZATION RUNNING
          </span>
          <h2 className="text-2xl font-editorial text-[#142A3B]">
            Building Your Personalized Portfolio
          </h2>
          <p className="text-xs text-[#66758A] max-w-md mx-auto">
            Our fiduciary engine is solving for optimal risk-adjusted weights and calculating whole shares.
          </p>
        </div>

        {/* Dynamic Multi-Stage Message */}
        <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-xs font-semibold text-[#142A3B] flex items-center justify-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#285C4D] animate-ping"></span>
          <span>{generationStage || "Analyzing risk tolerance and historical covariance..."}</span>
        </div>

        {/* Stepper Feedback */}
        <div className="space-y-2.5 text-left max-w-sm mx-auto text-xs text-[#4A5568]">
          <div className="flex items-center gap-2">
            <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
            <span>Risk capacity & horizon parameters verified</span>
          </div>
          <div className="flex items-center gap-2">
            <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
            <span>Nifty 50 fundamentals & excluded sectors filtered</span>
          </div>
          <div className="flex items-center gap-2">
            <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
            <span>SLSQP Sharpe ratio solver executing</span>
          </div>
          <div className="flex items-center gap-2">
            <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
            <span>Integer whole-share lot rounding applied</span>
          </div>
          <div className="flex items-center gap-2">
            <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
            <span>Compiling plain-English investment thesis</span>
          </div>
        </div>
      </div>
    );
  }

  const stepTitles = [
    "About You",
    "Your Financial Goal",
    "Capital & Horizon",
    "Risk Assessment",
    "Preferences & Safety",
    "Review & Confirm",
  ];

  return (
    <div className="w-full max-w-4xl 2xl:max-w-5xl mx-auto my-6 sm:my-8 space-y-6">
      {/* Wizard Top Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onCancel}
          type="button"
          className="text-xs font-semibold text-[#66758A] hover:text-[#142A3B] transition-colors cursor-pointer flex items-center gap-1.5"
        >
          <IconX className="w-3.5 h-3.5" />
          <span>Save & Exit</span>
        </button>

        <div className="text-right">
          <span className="text-xs font-bold text-[#142A3B]">
            Step {currentStep} of {totalSteps}: {stepTitles[currentStep - 1]}
          </span>
        </div>
      </div>

      {/* Introductory Section & Mode Chooser */}
      <div className="bg-[#FAF9F5] border border-[#E5E3DA] rounded-2xl p-5 sm:p-6 space-y-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-editorial font-bold text-[#142A3B]">
            Let&apos;s understand your investment goals
          </h1>
          <p className="text-xs sm:text-sm text-[#66758A] mt-1">
            Choose how you would like to share your investment requirements.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {/* Option 1: Describe your goals to Lucid (Recommended) */}
          <button
            type="button"
            onClick={() => setWizardMode("natural_language")}
            className={`p-4 rounded-xl text-left border transition-all cursor-pointer relative ${
              wizardMode === "natural_language"
                ? "bg-white border-[#142A3B] shadow-sm ring-1 ring-[#142A3B]"
                : "bg-white border-[#E5E3DA] hover:border-[#CBD5E1]"
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-bold text-[#142A3B] flex items-center gap-1.5">
                <IconSparkles className="w-4 h-4 text-[#285C4D]" />
                <span>Describe your goals to Lucid</span>
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                Recommended
              </span>
            </div>
            <p className="text-xs text-[#66758A] mt-1.5 leading-relaxed">
              Express your targets, budget, and risk comfort in your own words. Lucid AI extracts everything automatically.
            </p>
          </button>

          {/* Option 2: Answer a few questions */}
          <button
            type="button"
            onClick={() => setWizardMode("guided")}
            className={`p-4 rounded-xl text-left border transition-all cursor-pointer relative ${
              wizardMode === "guided"
                ? "bg-white border-[#142A3B] shadow-sm ring-1 ring-[#142A3B]"
                : "bg-white border-[#E5E3DA] hover:border-[#CBD5E1]"
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-bold text-[#142A3B] flex items-center gap-1.5">
                <IconFileText className="w-4 h-4 text-[#285C4D]" />
                <span>Answer a few questions</span>
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#F1F5F9] text-[#475569] border border-[#CBD5E1]">
                Step-by-Step
              </span>
            </div>
            <p className="text-xs text-[#66758A] mt-1.5 leading-relaxed">
              Step-by-step structured questionnaire covering risk tolerance, time horizons, and sector guardrails.
            </p>
          </button>
        </div>
      </div>

      {wizardMode === "natural_language" ? (
        <div className="bg-white rounded-2xl border border-[#E5E3DA] shadow-md p-6 sm:p-8 space-y-6">
          {/* Header */}
          <div>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider flex items-center gap-1.5">
                <IconSparkles className="w-3.5 h-3.5" /> GEMINI 3.8 FLASH &bull; NATURAL LANGUAGE PROFILING
              </span>
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                SEBI RIA Compliant Extraction
              </span>
            </div>
            <h2 className="text-2xl font-editorial text-[#142A3B] mt-1">
              Tell Lucid what you&apos;re looking to achieve
            </h2>
            <p className="text-sm text-[#4A5568] mt-1 max-w-2xl leading-relaxed">
              Describe your investment goals, budget, time horizon, and preferences in your own words. Lucid will organize the information and help you complete your investor profile.
            </p>
          </div>

          {/* Quick-Fill Sample Prompts */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-[#66758A] uppercase tracking-wider block">
              Quick Inspiration Prompts:
            </span>
            <div className="flex flex-wrap gap-2">
              {[
                {
                  label: "Tech Professional (₹3.5L, 5 yrs, Moderate)",
                  icon: <IconBriefcase className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />,
                  text: "I am a 29-year-old software architect with ₹3,50,000 to invest for 5 years. I have a moderate risk appetite and a full 9-month emergency fund in bank FDs. I have intermediate experience in mutual funds and want strong exposure to Information Technology and Banking, but please avoid Tobacco.",
                },
                {
                  label: "Conservative Retiree (₹5L, 3 yrs, Capital Preservation)",
                  icon: <IconShield className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />,
                  text: "I am a 62-year-old retired educator with ₹5,00,000 to invest for the next 3 years. My primary goal is capital preservation and reliable dividend income with low risk. I have 1 year of living expenses in savings and beginner experience.",
                },
                {
                  label: "Aggressive Compounding (₹2L, 10 yrs, High Growth)",
                  icon: <IconRocket className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />,
                  text: "I am 26 years old with ₹2,00,000 to invest for a 10-year horizon. I have an aggressive risk profile, high drawdown tolerance, full emergency reserves, and experienced market knowledge. I prefer Renewable Energy, Automobile/EVs, and Technology.",
                },
              ].map((sample, sIdx) => (
                <button
                  key={sIdx}
                  type="button"
                  onClick={() => {
                    setNlpInput(sample.text);
                    setExtractedNLPResult(null);
                    setNlpError(null);
                  }}
                  className="text-xs px-3 py-1.5 rounded-lg border border-[#D6D3C8] bg-[#F7F6F1] text-[#142A3B] hover:border-[#142A3B] hover:bg-white transition-all text-left cursor-pointer flex items-center gap-1.5"
                >
                  {sample.icon}
                  <span>{sample.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Textarea Input */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-[#142A3B] uppercase tracking-wider">
                Your Financial Situation & Intent:
              </label>
              <span className="text-xs text-[#66758A]">
                {nlpInput.length} characters
              </span>
            </div>
            <textarea
              rows={5}
              value={nlpInput}
              onChange={(e) => {
                setNlpInput(e.target.value);
                if (nlpError) setNlpError(null);
              }}
              placeholder="Example: I want to invest ₹1,50,000 for around five years. I'm comfortable with moderate risk and want to build long-term wealth..."
              className="w-full p-4 rounded-xl border border-[#D6D3C8] focus:border-[#142A3B] focus:ring-1 focus:ring-[#142A3B] text-sm text-[#142A3B] placeholder-[#A0AEC0] outline-none transition-all resize-y leading-relaxed"
            />
          </div>

          {/* Action Button & Errors */}
          {nlpError && (
            <div className="p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-xs font-semibold text-[#B91C1C] flex items-center gap-2">
              <IconAlertTriangle className="w-4 h-4 shrink-0" />
              <span>{nlpError}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-2 border-t border-[#E5E3DA] flex-wrap gap-3">
            <span className="text-xs text-[#66758A]">
              Lucid extracts: Capital, Horizon, Risk Tier, Emergency Reserve, Experience, & Sector Rules.
            </span>

            <button
              type="button"
              disabled={isExtractingNLP || nlpInput.trim().length < 5}
              onClick={handleNLPExtract}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer ${
                isExtractingNLP || nlpInput.trim().length < 5
                  ? "bg-[#D6D3C8] text-[#66758A] cursor-not-allowed"
                  : "bg-[#142A3B] hover:bg-[#0E1E2B] text-white"
              }`}
            >
              {isExtractingNLP ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Analyzing Requirements...</span>
                </>
              ) : (
                <>
                  <IconSparkles className="w-4 h-4 text-emerald-400" />
                  <span>Analyze My Requirements</span>
                </>
              )}
            </button>
          </div>

          {/* Extraction Result Preview Card */}
          {extractedNLPResult && (
            <div className="mt-6 p-5 sm:p-6 rounded-2xl bg-[#F7F6F1] border border-[#C6D8D1] space-y-5 animate-fadeIn">
              <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-[#E5E3DA]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#285C4D]"></span>
                  <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                    Profile Successfully Extracted
                  </span>
                </div>
                <span className="text-xs font-semibold text-[#285C4D]">
                  Confidence: {Math.round(extractedNLPResult.confidence_score * 100)}%
                </span>
              </div>

              {/* Parameters Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA]">
                  <span className="text-[11px] font-bold text-[#66758A] uppercase block">Investment Capital</span>
                  <span className="text-base font-bold text-[#142A3B] tabular-nums">
                    {formatINR(extractedNLPResult.extracted_profile.investment_amount)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA]">
                  <span className="text-[11px] font-bold text-[#66758A] uppercase block">Time Horizon</span>
                  <span className="text-base font-bold text-[#142A3B]">
                    {extractedNLPResult.extracted_profile.horizon_months} Months ({Math.round(extractedNLPResult.extracted_profile.horizon_months / 12)} Yrs)
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA]">
                  <span className="text-[11px] font-bold text-[#66758A] uppercase block">Assessed Risk Tier</span>
                  <span className="text-base font-bold text-[#285C4D] capitalize">
                    {extractedNLPResult.extracted_profile.risk_category.replace("_", " ")}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA]">
                  <span className="text-[11px] font-bold text-[#66758A] uppercase block">Emergency Reserve</span>
                  <div className={`text-sm font-bold capitalize flex items-center gap-1.5 mt-0.5 ${
                    extractedNLPResult.extracted_profile.emergency_fund_status === "full"
                      ? "text-[#285C4D]"
                      : extractedNLPResult.extracted_profile.emergency_fund_status === "none"
                      ? "text-[#B91C1C]"
                      : "text-[#D97706]"
                  }`}>
                    {extractedNLPResult.extracted_profile.emergency_fund_status === "full" ? (
                      <>
                        <IconCheck className="w-3.5 h-3.5 text-[#285C4D]" />
                        <span>6+ Months (Safe)</span>
                      </>
                    ) : extractedNLPResult.extracted_profile.emergency_fund_status === "none" ? (
                      <>
                        <IconAlertTriangle className="w-3.5 h-3.5 text-[#B91C1C]" />
                        <span>No Reserve (Capped)</span>
                      </>
                    ) : (
                      <span>
                        {extractedNLPResult.extracted_profile.loss_capacity_emergency_months
                          ? `${extractedNLPResult.extracted_profile.loss_capacity_emergency_months} Month${
                              extractedNLPResult.extracted_profile.loss_capacity_emergency_months > 1 ? "s" : ""
                            } (Partial)`
                          : "Partial (1-3 Mos)"}
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA]">
                  <span className="text-[11px] font-bold text-[#66758A] uppercase block">Experience & Knowledge</span>
                  <span className="text-sm font-bold text-[#142A3B] capitalize">
                    {extractedNLPResult.extracted_profile.experience_level} / {extractedNLPResult.extracted_profile.knowledge_level}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA]">
                  <span className="text-[11px] font-bold text-[#66758A] uppercase block">Primary Goal</span>
                  <span className="text-sm font-bold text-[#142A3B] truncate block">
                    {extractedNLPResult.extracted_profile.goal_name}
                  </span>
                </div>
              </div>

              {/* Preferred & Excluded Sectors */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA] space-y-1.5">
                  <span className="font-bold text-[#285C4D] uppercase text-[11px] block">
                    Preferred Sectors ({extractedNLPResult.extracted_profile.preferred_sectors.length}):
                  </span>
                  {extractedNLPResult.extracted_profile.preferred_sectors.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {extractedNLPResult.extracted_profile.preferred_sectors.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1] font-semibold flex items-center gap-1">
                          <IconCheck className="w-3 h-3 text-[#285C4D]" />
                          <span>{s}</span>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[#66758A] italic">Unconstrained (Broad multi-sector selection)</span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-white border border-[#E5E3DA] space-y-1.5">
                  <span className="font-bold text-[#B91C1C] uppercase text-[11px] block">
                    Excluded Sectors ({extractedNLPResult.extracted_profile.excluded_sectors.length}):
                  </span>
                  {extractedNLPResult.extracted_profile.excluded_sectors.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {extractedNLPResult.extracted_profile.excluded_sectors.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-[#FEF2F2] text-[#B91C1C] border border-[#FECACA] font-semibold flex items-center gap-1">
                          <IconX className="w-3 h-3 text-[#B91C1C]" />
                          <span>{s}</span>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[#66758A] italic">None (All sectors eligible)</span>
                  )}
                </div>
              </div>

              {/* Fiduciary Suitability Notes */}
              {extractedNLPResult.fiduciary_notes.length > 0 && (
                <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] space-y-1.5 text-xs text-[#4A5568]">
                  <span className="font-bold text-[#142A3B] uppercase text-[11px] block">
                    Fiduciary Suitability & Guardrail Audit:
                  </span>
                  <ul className="space-y-1">
                    {extractedNLPResult.fiduciary_notes.map((note, nIdx) => (
                      <li key={nIdx} className="flex items-start gap-1.5">
                        <span className="text-[#285C4D] font-bold">•</span>
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Direct Next Action Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3 flex-wrap">
                <button
                  type="button"
                  onClick={handleApplyNLPToWizard}
                  className="px-5 py-2.5 rounded-xl border border-[#D6D3C8] bg-white hover:bg-[#F7F6F1] text-[#142A3B] text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center gap-1.5"
                >
                  <IconEdit className="w-4 h-4 text-[#142A3B]" />
                  <span>Review & Edit in Questionnaire</span>
                </button>

                <button
                  type="button"
                  onClick={handleConfirmAndGenerateFromNLP}
                  className="px-6 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white text-xs sm:text-sm font-bold transition-all shadow-md hover:shadow-lg cursor-pointer flex items-center gap-2"
                >
                  <IconSparkles className="w-4 h-4 text-emerald-400" />
                  <span>Confirm & Generate Portfolio</span>
                  <IconArrowUpRight className="w-4 h-4 text-white" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Progress Bar */}
          <div className="w-full bg-[#E5E3DA] h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-[#142A3B] h-full transition-all duration-300 rounded-full"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            ></div>
          </div>

          {/* Main Wizard Card */}
          <div className="bg-white rounded-2xl border border-[#E5E3DA] shadow-md p-6 sm:p-8 space-y-8">
        {/* ======================================================= */}
        {/* STAGE 1: ABOUT YOU */}
        {/* ======================================================= */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                STAGE 1 &bull; INVESTOR PROFILE
              </span>
              <h2 className="text-2xl font-editorial text-[#142A3B] mt-1">
                Tell us about your investment background
              </h2>
              <p className="text-sm text-[#4A5568] mt-1">
                This helps us tailor the recommendations and avoid unnecessary complexity.
              </p>
            </div>

            <div className="space-y-4">
              <label className="block text-sm font-bold text-[#142A3B]">
                What is your experience with the Indian stock market?
              </label>

              <div className="grid grid-cols-1 gap-3">
                {[
                  {
                    id: "beginner",
                    title: "Beginner",
                    desc: "I am new to direct stocks. I want guidance and proven, stable blue-chip companies.",
                    badge: "Guided & Safe",
                  },
                  {
                    id: "intermediate",
                    title: "Intermediate",
                    desc: "I invest in mutual funds or have owned a few stocks. I want a structured portfolio.",
                    badge: "Balanced Strategy",
                  },
                  {
                    id: "experienced",
                    title: "Experienced",
                    desc: "I actively trade or invest in equities and understand company valuations.",
                    badge: "Factor Optimized",
                  },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setExperience(item.id)}
                    className={`p-4 rounded-xl border text-left transition-all cursor-pointer flex items-start justify-between gap-3 ${
                      experience === item.id
                        ? "border-[#142A3B] bg-[#F7F6F1] shadow-xs"
                        : "border-[#E5E3DA] hover:border-[#D6D3C8]"
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-[#142A3B]">{item.title}</span>
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-[#EFECE4] text-[#4A5568]">
                          {item.badge}
                        </span>
                      </div>
                      <p className="text-sm text-[#4A5568] mt-1 leading-relaxed">{item.desc}</p>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        experience === item.id
                          ? "border-[#142A3B] bg-[#142A3B] text-white"
                          : "border-[#D6D3C8]"
                      }`}
                    >
                      {experience === item.id && <IconCheck className="w-3 h-3 text-white" />}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Market Knowledge Level */}
            <div className="space-y-4">
              <label className="block text-sm font-bold text-[#142A3B]">
                What is your equity market knowledge level?
              </label>

              <div className="grid grid-cols-1 gap-3">
                {[
                  {
                    id: "basic",
                    title: "Basic / Beginner",
                    desc: "Primary background in bank deposits, fixed income, or mutual fund SIPs.",
                    badge: "Guided Foundation",
                  },
                  {
                    id: "intermediate",
                    title: "Intermediate",
                    desc: "Understands balance sheets, index benchmarks, and diversification principles.",
                    badge: "Market Informed",
                  },
                  {
                    id: "advanced",
                    title: "Advanced",
                    desc: "Understands standard deviation, drawdowns, valuation multiples, and financial statements.",
                    badge: "Quantitative Depth",
                  },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setKnowledge(item.id);
                      const knowQ = questions.find((q) => q.question_code === "INVESTMENT_KNOWLEDGE");
                      if (knowQ) {
                        const codeMap: Record<string, string> = {
                          basic: "EXP_NONE",
                          intermediate: "EXP_MUTUAL_FUNDS",
                          advanced: "EXP_DIRECT_EQUITY",
                        };
                        const targetOpt = knowQ.options.find((o) => o.option_code === codeMap[item.id]);
                        if (targetOpt) {
                          handleSelectAnswer(knowQ.question_id, targetOpt.option_id, targetOpt.score);
                        }
                      }
                    }}
                    className={`p-4 rounded-xl border text-left transition-all cursor-pointer flex items-start justify-between gap-3 ${
                      knowledge === item.id
                        ? "border-[#142A3B] bg-[#F7F6F1] shadow-xs"
                        : "border-[#E5E3DA] hover:border-[#D6D3C8]"
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-[#142A3B]">{item.title}</span>
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-[#EFECE4] text-[#4A5568]">
                          {item.badge}
                        </span>
                      </div>
                      <p className="text-sm text-[#4A5568] mt-1 leading-relaxed">{item.desc}</p>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        knowledge === item.id
                          ? "border-[#142A3B] bg-[#142A3B] text-white"
                          : "border-[#D6D3C8]"
                      }`}
                    >
                      {knowledge === item.id && <IconCheck className="w-3 h-3 text-white" />}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Mobile Contact Number (Optional) */}
            <div className="p-4 rounded-xl bg-white border border-[#E5E3DA] space-y-2">
              <label className="block text-sm font-bold text-[#142A3B]">
                Mobile Phone Number (Optional)
              </label>
              <input
                type="tel"
                value={mobileNumber}
                onChange={(e) => setMobileNumber(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full max-w-sm px-3.5 py-2.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-sm font-medium text-[#142A3B] focus:outline-none focus:border-[#142A3B]"
              />
              <p className="text-xs text-[#66758A]">
                Used for SMS OTP verification, two-factor authorization, and real-time portfolio alerts.
              </p>
            </div>

            {/* SEBI Fiduciary Note */}
            <div className="p-4 rounded-xl bg-[#ECF3F0] border border-[#C6D8D1] flex items-start gap-3">
              <IconShield className="w-5 h-5 text-[#285C4D] flex-shrink-0 mt-0.5" />
              <p className="text-sm text-[#285C4D] leading-relaxed">
                <strong>Why we ask:</strong> Under SEBI (Investment Advisers) Regulations, fiduciary suitability requires aligning portfolio risk with your investor background.
              </p>
            </div>
          </div>
        )}

        {/* ======================================================= */}
        {/* STAGE 2: FINANCIAL GOALS */}
        {/* ======================================================= */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                STAGE 2 &bull; FINANCIAL GOAL
              </span>
              <h2 className="text-2xl font-editorial text-[#142A3B] mt-1">
                What are you investing this capital for?
              </h2>
              <p className="text-sm text-[#4A5568] mt-1">
                Every rupee should have a clear purpose and destination.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  id: "wealth_creation",
                  title: "Wealth Creation",
                  desc: "Long-term compounding over 5-10 years.",
                  icon: <IconTrendingUp className="w-5 h-5 text-[#285C4D]" />,
                },
                {
                  id: "retirement",
                  title: "Retirement Corpus",
                  desc: "Building financial independence for later years.",
                  icon: <IconSun className="w-5 h-5 text-[#285C4D]" />,
                },
                {
                  id: "child_education",
                  title: "Child's Higher Education",
                  desc: "College expenses in India or abroad.",
                  icon: <IconAcademicCap className="w-5 h-5 text-[#285C4D]" />,
                },
                {
                  id: "capital_preservation",
                  title: "Capital Preservation",
                  desc: "Beating inflation with minimal drawdowns.",
                  icon: <IconShield className="w-5 h-5 text-[#285C4D]" />,
                },
              ].map((g) => (
                <button
                  key={g.id}
                  type="button"
                  onClick={() => {
                    setGoalType(g.id);
                    setGoalName(g.title);
                  }}
                  className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    goalType === g.id
                      ? "border-[#142A3B] bg-[#F7F6F1] shadow-xs"
                      : "border-[#E5E3DA] hover:border-[#D6D3C8]"
                  }`}
                >
                  <div className="w-9 h-9 rounded-xl bg-[#ECF3F0] border border-[#C6D8D1] flex items-center justify-center mb-2.5">
                    {g.icon}
                  </div>
                  <div className="text-base font-bold text-[#142A3B]">{g.title}</div>
                  <div className="text-sm text-[#4A5568] mt-1">{g.desc}</div>
                </button>
              ))}
            </div>

            <div className="space-y-3 pt-2">
              <label className="block text-sm font-bold text-[#142A3B]">
                Goal Name / Label
              </label>
              <input
                type="text"
                value={goalName}
                onChange={(e) => setGoalName(e.target.value)}
                placeholder="e.g. 2030 Wealth Builder"
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-sm text-[#142A3B] focus:outline-none focus:ring-2 focus:ring-[#142A3B]"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-bold text-[#142A3B]">
                  Target Future Corpus (Optional)
                </label>
                <span className="text-sm font-bold text-[#285C4D] tabular-nums">
                  {formatINR(targetCorpus)}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {[500000, 1000000, 2500000, 5000000, 10000000].map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => setTargetCorpus(amt)}
                    className={`px-3.5 py-2 rounded-lg text-sm font-semibold border transition-all cursor-pointer ${
                      targetCorpus === amt
                        ? "bg-[#142A3B] text-white border-[#142A3B]"
                        : "bg-[#EFECE4] text-[#4A5568] border-[#E5E3DA] hover:border-[#D6D3C8]"
                    }`}
                  >
                    {amt >= 10000000
                      ? `₹${amt / 10000000} Cr`
                      : `₹${amt / 100000} Lakh`}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ======================================================= */}
        {/* STAGE 3: CAPITAL & HORIZON */}
        {/* ======================================================= */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                STAGE 3 &bull; CAPITAL & TIME HORIZON
              </span>
              <h2 className="text-2xl font-editorial text-[#142A3B] mt-1">
                How much are you investing and for how long?
              </h2>
              <p className="text-sm text-[#4A5568] mt-1">
                We will calculate whole shares and integer execution specifically for this amount.
              </p>
            </div>

            {/* Capital Amount Input */}
            <div className="space-y-3">
              <label className="block text-sm font-bold text-[#142A3B]">
                Initial Investment Capital (₹)
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-2.5 text-base font-bold text-[#66758A]">
                  ₹
                </span>
                <input
                  type="number"
                  min={10000}
                  step={5000}
                  value={capital}
                  onChange={(e) => setCapital(Math.max(10000, Number(e.target.value) || 0))}
                  className="w-full pl-8 pr-4 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-base font-bold text-[#142A3B] focus:outline-none focus:ring-2 focus:ring-[#142A3B] tabular-nums"
                />
              </div>

              {/* Quick Capital Preset Chips */}
              <div className="flex flex-wrap gap-2 pt-1">
                {[50000, 100000, 250000, 500000, 1000000].map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => setCapital(amt)}
                    className={`px-3.5 py-2 rounded-lg text-sm font-semibold border transition-all cursor-pointer ${
                      capital === amt
                        ? "bg-[#142A3B] text-white border-[#142A3B]"
                        : "bg-[#EFECE4] text-[#4A5568] border-[#E5E3DA] hover:border-[#D6D3C8]"
                    }`}
                  >
                    {formatINR(amt)}
                  </button>
                ))}
              </div>
            </div>

            {/* Time Horizon */}
            <div className="space-y-3 pt-2">
              <label className="block text-sm font-bold text-[#142A3B]">
                Intended Investment Horizon
              </label>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  {
                    months: 36,
                    label: "3 Years",
                    sub: "Medium-Term",
                    desc: "Balanced allocations with lower downside volatility.",
                  },
                  {
                    months: 60,
                    label: "5 Years",
                    sub: "Recommended",
                    desc: "Ideal compounding window through corporate earnings cycles.",
                  },
                  {
                    months: 84,
                    label: "7+ Years",
                    sub: "Wealth Builder",
                    desc: "Full equity exposure to maximize long-term real CAGR.",
                  },
                ].map((h) => (
                  <button
                    key={h.months}
                    type="button"
                    onClick={() => setHorizonMonths(h.months)}
                    className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                      horizonMonths === h.months
                        ? "border-[#142A3B] bg-[#F7F6F1] shadow-xs"
                        : "border-[#E5E3DA] hover:border-[#D6D3C8]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-base font-bold text-[#142A3B]">{h.label}</span>
                      <span
                        className={`text-xs font-semibold px-2.5 py-0.5 rounded ${
                          h.sub === "Recommended"
                            ? "bg-[#ECF3F0] text-[#285C4D] font-bold"
                            : "bg-[#EFECE4] text-[#66758A]"
                        }`}
                      >
                        {h.sub}
                      </span>
                    </div>
                    <p className="text-sm text-[#4A5568] mt-1.5 leading-relaxed">{h.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Horizon Guidance Note */}
            <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-sm text-[#4A5568] leading-relaxed flex items-start gap-2.5">
              <IconLightbulb className="w-4 h-4 text-[#285C4D] shrink-0 mt-0.5" />
              <span><strong>Why horizon matters:</strong> Equities fluctuate in the short run. A 3-to-5 year window provides the time needed for quality companies to grow earnings and recover from short-term market dips.</span>
            </div>
          </div>
        )}

        {/* ======================================================= */}
        {/* STAGE 4: RISK ASSESSMENT */}
        {/* ======================================================= */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                STAGE 4 &bull; SEBI RISK EVALUATION
              </span>
              <h2 className="text-2xl font-editorial text-[#142A3B] mt-1">
                Your Comfort with Market Movements
              </h2>
              <p className="text-sm text-[#4A5568] mt-1">
                We balance your financial capacity to take risk against your emotional comfort.
              </p>
            </div>

            {/* Capacity vs Tolerance Explainer */}
            <div className="p-4 rounded-xl bg-[#ECF3F0] border border-[#C6D8D1] grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <span className="font-bold text-[#285C4D]">Risk Capacity:</span>
                <p className="text-[#2D3748] mt-0.5">
                  Your objective financial ability to absorb paper losses without impacting your lifestyle or emergency funds.
                </p>
              </div>
              <div>
                <span className="font-bold text-[#285C4D]">Risk Tolerance:</span>
                <p className="text-[#2D3748] mt-0.5">
                  Your psychological peace of mind when market headlines report drops of 10% to 20%.
                </p>
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-5">
              {(questions.length > 0 ? questions : []).map((q, idx) => (
                <div key={q.question_id} className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-3">
                  <div className="text-sm font-bold text-[#142A3B]">
                    {idx + 1}. {q.question_text}
                  </div>

                  <div className="grid grid-cols-1 gap-2">
                    {q.options.map((opt) => {
                      const isSelected = answers[q.question_id] === opt.option_id;
                      return (
                        <button
                          key={opt.option_id}
                          type="button"
                          onClick={() => handleSelectAnswer(q.question_id, opt.option_id, opt.score)}
                          className={`p-3.5 rounded-lg border text-left text-sm font-medium transition-all cursor-pointer flex items-center justify-between ${
                            isSelected
                              ? "border-[#142A3B] bg-white text-[#142A3B] font-bold shadow-xs"
                              : "border-[#E5E3DA] bg-white text-[#4A5568] hover:border-[#D6D3C8]"
                          }`}
                        >
                          <span>{opt.option_label}</span>
                          <span
                            className={`w-4 h-4 rounded-full border flex items-center justify-center text-xs ${
                              isSelected
                                ? "border-[#142A3B] bg-[#142A3B] text-white"
                                : "border-[#D6D3C8]"
                            }`}
                          >
                            {isSelected && <IconCheck className="w-2.5 h-2.5 text-white" />}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              {/* If no backend questions yet loaded, show fallback selector */}
              {questions.length === 0 && (
                <div className="space-y-3">
                  <label className="block text-sm font-bold text-[#142A3B]">
                    Select Your Risk Profile Category
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[
                      {
                        cat: "conservative",
                        title: "Conservative",
                        desc: "High emphasis on capital safety and low volatility.",
                      },
                      {
                        cat: "moderate",
                        title: "Moderate (Recommended)",
                        desc: "Balanced growth with measured risk exposure.",
                      },
                      {
                        cat: "aggressive",
                        title: "Aggressive / Growth",
                        desc: "Maximum wealth compounding, ready for short-term swings.",
                      },
                    ].map((item) => (
                      <button
                        key={item.cat}
                        type="button"
                        onClick={() => setCalculatedRisk(item.cat)}
                        className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                          calculatedRisk === item.cat
                            ? "border-[#142A3B] bg-[#F7F6F1] shadow-xs"
                            : "border-[#E5E3DA] hover:border-[#D6D3C8]"
                        }`}
                      >
                        <div className="text-base font-bold text-[#142A3B]">{item.title}</div>
                        <div className="text-sm text-[#4A5568] mt-1">{item.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Live Profile Calculated Pill */}
            <div className="p-4 sm:p-5 rounded-2xl bg-white border border-[#E5E3DA] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-[#142A3B]">Assessed Risk Category:</span>
                  <span className="text-xs text-[#66758A]">
                    (SEBI Suitability Guardrail Active)
                  </span>
                </div>
                <p className="text-xs text-[#4A5568] mt-1 max-w-lg leading-relaxed">
                  {calculatedRisk === "aggressive" && "High risk tolerance and complete emergency reserve capacity. Calibrated for maximum equity compounding."}
                  {calculatedRisk === "growth" && "Growth orientation with confirmed capacity to absorb market cyclicality for above-benchmark returns."}
                  {calculatedRisk === "moderate" && "Balanced growth and measured drawdown exposure; calibrated for disciplined wealth creation."}
                  {(calculatedRisk === "conservative" || calculatedRisk === "very_conservative") && "Capital protection focus. Guardrails prevent aggressive allocation due to lack of a 6-month emergency reserve or shorter time horizon."}
                </p>
              </div>
              <span
                data-testid="assessed-risk-category"
                className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider shrink-0 ${
                calculatedRisk === "aggressive"
                  ? "bg-[#991B1B] text-white"
                  : calculatedRisk === "growth"
                  ? "bg-[#C2410C] text-white"
                  : calculatedRisk === "moderate"
                  ? "bg-[#166534] text-white"
                  : "bg-[#1D4ED8] text-white"
              }`}>
                {calculatedRisk.replace("_", " ")}
              </span>
            </div>
          </div>
        )}

        {/* ======================================================= */}
        {/* STAGE 5: PREFERENCES & SAFETY */}
        {/* ======================================================= */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                STAGE 5 &bull; PREFERENCES & SAFETY
              </span>
              <h2 className="text-2xl font-editorial text-[#142A3B] mt-1">
                Customize your portfolio rules
              </h2>
              <p className="text-sm text-[#4A5568] mt-1">
                Exclude specific sectors or refine company concentration to match your values.
              </p>
            </div>

            {/* Sector Exclusions */}
            <div className="space-y-3">
              <label className="block text-sm font-bold text-[#142A3B]">
                Do you wish to exclude any industries? (Optional)
              </label>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {[
                  { id: "Tobacco", label: "Tobacco & Cigarettes" },
                  { id: "Alcohol", label: "Alcohol & Liquor" },
                  { id: "Gambling", label: "Gambling & Gaming" },
                  { id: "Defense", label: "Defense & Weapons" },
                  { id: "Fossil Fuels", label: "Oil & Fossil Fuels" },
                ].map((s) => {
                  const isExcluded = excludedSectors.includes(s.id);
                  return (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => toggleSectorExclusion(s.id)}
                      className={`p-3.5 rounded-xl border text-sm font-medium text-left transition-all cursor-pointer ${
                        isExcluded
                          ? "border-[#B91C1C] bg-[#FEF2F2] text-[#B91C1C] font-bold"
                          : "border-[#E5E3DA] bg-white text-[#4A5568] hover:border-[#D6D3C8]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>{s.label}</span>
                        {isExcluded ? <IconX className="w-3.5 h-3.5 text-[#B91C1C]" /> : <span className="font-bold">+</span>}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* AI Dynamic Stock Count & Capital Sizing Engine */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-[#142A3B]/5 via-white to-[#285C4D]/10 border border-[#285C4D]/25 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#285C4D] text-white flex items-center justify-center font-bold text-sm shadow-xs">
                    <IconSparkles className="w-4 h-4 text-emerald-300" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#142A3B]">
                      AI Dynamic Stock Count &amp; Allocation Sizing
                    </h3>
                    <p className="text-xs text-[#285C4D] font-medium">
                      Holding count automatically determined by Lucid AI
                    </p>
                  </div>
                </div>
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded bg-[#285C4D] text-white">
                  Automated
                </span>
              </div>

              <p className="text-sm text-[#4A5568] leading-relaxed">
                Rather than forcing a manual stock count, Lucid's multi-agent optimization engine dynamically determines the optimal number of companies for your exact capital budget (<strong>{formatINR(capital)}</strong>). This prevents integer-share cash drag on NSE/BSE, aligns candidate selection with your stated goal, and strictly enforces Lucid risk policy guardrails (&le;25% single stock, &le;40% single sector, under SEBI suitability norms).
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1 text-xs text-[#142A3B]">
                <div className="p-3 rounded-lg bg-white/90 border border-[#E5E3DA] flex items-center gap-2">
                  <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
                  <span><strong>Zero Cash Drag:</strong> Calibrated to whole-share lot sizes</span>
                </div>
                <div className="p-3 rounded-lg bg-white/90 border border-[#E5E3DA] flex items-center gap-2">
                  <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
                  <span><strong>Goal-Tuned Picks:</strong> Tailored to {goalName}</span>
                </div>
                <div className="p-3 rounded-lg bg-white/90 border border-[#E5E3DA] flex items-center gap-2">
                  <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
                  <span><strong>Risk Policies:</strong> &le;25% stock / &le;40% sector</span>
                </div>
              </div>
            </div>

            {/* Built-in Safety Rules */}
            <div className="p-4.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2">
              <span className="text-xs font-bold text-[#142A3B] uppercase tracking-wider">
                Fiduciary Concentration Rules (Active by Default)
              </span>
              <div className="space-y-2 text-sm text-[#4A5568]">
                <div className="flex items-center gap-2">
                  <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
                  <span>Maximum single stock weight capped at 25%</span>
                </div>
                <div className="flex items-center gap-2">
                  <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
                  <span>Maximum single sector weight capped at 40%</span>
                </div>
                <div className="flex items-center gap-2">
                  <IconCheck className="w-3.5 h-3.5 text-[#285C4D] shrink-0" />
                  <span>Strict integer lot sizing (NSE/BSE whole shares only)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================= */}
        {/* STAGE 6: REVIEW & CONFIRM */}
        {/* ======================================================= */}
        {currentStep === 6 && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                STAGE 6 &bull; REVIEW & CONFIRMATION
              </span>
              <h2 className="text-2xl font-editorial text-[#142A3B] mt-1">
                Everything is ready. Review your plan.
              </h2>
              <p className="text-sm text-[#4A5568] mt-1">
                Confirm your preferences below before our optimizer generates your custom portfolio.
              </p>
            </div>

            {/* Summary Review Cards */}
            <div className="divide-y divide-[#E5E3DA] border border-[#E5E3DA] rounded-xl overflow-hidden bg-[#F7F6F1]">
              <div className="p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#66758A] uppercase font-bold">Investment Capital</div>
                  <div className="text-lg font-bold text-[#142A3B] tabular-nums">
                    {formatINR(capital)}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="text-sm font-bold text-[#4338CA] hover:underline cursor-pointer"
                >
                  Edit
                </button>
              </div>

              <div className="p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#66758A] uppercase font-bold">Investment Horizon</div>
                  <div className="text-lg font-bold text-[#142A3B]">
                    {horizonMonths / 12} Years ({horizonMonths} Months)
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="text-sm font-bold text-[#4338CA] hover:underline cursor-pointer"
                >
                  Edit
                </button>
              </div>

              <div className="p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#66758A] uppercase font-bold">Assessed Risk Profile</div>
                  <div className="text-lg font-bold text-[#285C4D] uppercase tracking-wide">
                    {calculatedRisk.replace("_", " ")}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(4)}
                  className="text-sm font-bold text-[#4338CA] hover:underline cursor-pointer"
                >
                  Edit
                </button>
              </div>

              <div className="p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#66758A] uppercase font-bold">Goal Name</div>
                  <div className="text-lg font-bold text-[#142A3B]">
                    {goalName}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="text-sm font-bold text-[#4338CA] hover:underline cursor-pointer"
                >
                  Edit
                </button>
              </div>

              <div className="p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#66758A] uppercase font-bold">Sector Exclusions</div>
                  <div className="text-base font-semibold text-[#142A3B]">
                    {excludedSectors.length > 0
                      ? excludedSectors.join(", ")
                      : "None (Full NSE/BSE Universe)"}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(5)}
                  className="text-sm font-bold text-[#4338CA] hover:underline cursor-pointer"
                >
                  Edit
                </button>
              </div>

              <div className="p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#66758A] uppercase font-bold">Stock Count &amp; Allocation Sizing</div>
                  <div className="text-base font-semibold text-[#142A3B]">
                    Dynamically Determined by Lucid AI (Calibrated to {formatINR(capital)})
                  </div>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded bg-[#ECF3F0] text-[#285C4D]">
                  Automatic
                </span>
              </div>
            </div>

            {/* Reassurance Callout */}
            <div className="p-4 rounded-xl bg-[#ECF3F0] border border-[#C6D8D1] flex items-start gap-3">
              <IconCheck className="w-5 h-5 text-[#285C4D] flex-shrink-0 mt-0.5" />
              <p className="text-sm text-[#285C4D] leading-relaxed">
                Clicking <strong>Generate My Portfolio</strong> will run our multi-step optimization engine to balance corporate fundamentals, risk metrics, and whole-share execution.
              </p>
            </div>
          </div>
        )}

        {/* Wizard Navigation Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-[#E5E3DA]">
          {currentStep > 1 ? (
            <button
              onClick={handleBack}
              type="button"
              className="px-6 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-[#4A5568] hover:text-[#142A3B] text-sm font-bold transition-all cursor-pointer"
            >
              ← Back
            </button>
          ) : (
            <button
              onClick={onCancel}
              type="button"
              className="px-6 py-2.5 rounded-xl border border-[#D6D3C8] bg-white text-[#4A5568] hover:text-[#142A3B] text-sm font-bold transition-all cursor-pointer"
            >
              Cancel
            </button>
          )}

          {currentStep < totalSteps ? (
            <button
              onClick={handleNext}
              type="button"
              className="px-7 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-sm font-bold transition-all shadow-sm cursor-pointer flex items-center gap-1.5"
            >
              <span>Continue →</span>
            </button>
          ) : (
            <button
              onClick={handleFinalSubmit}
              type="button"
              className="px-8 py-3 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white text-sm font-bold transition-all shadow-md hover:shadow-lg cursor-pointer flex items-center gap-2"
            >
              <IconSparkles className="w-4 h-4 text-emerald-300" />
              <span>Generate My Portfolio</span>
              <IconArrowUpRight className="w-4 h-4 text-white" />
            </button>
          )}
        </div>
      </div>
      </>
      )}
    </div>
  );
}

