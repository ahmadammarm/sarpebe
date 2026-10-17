import type { Metadata } from "next";
import { LessonPlanDashboard } from "@/components/features/lesson-plans/LessonPlanDashboard";

export const metadata: Metadata = { title: "Modul ajar saya" };

export default function LessonPlansPage() {
  return <LessonPlanDashboard />;
}
