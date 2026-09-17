"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { LessonPlan, getLessonPlan } from "@/lib/api/lesson-plans";
import { LessonPlanEditor } from "@/components/features/lesson-plans/LessonPlanEditor";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function LessonPlanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [plan, setPlan] = useState<LessonPlan | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getLessonPlan(id)
      .then((data) => setPlan(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="p-8 text-center">Memuat Rencana Pembelajaran...</div>;
  }

  if (!plan) {
    return <div className="p-8 text-center text-red-500">Rencana Pembelajaran tidak ditemukan.</div>;
  }

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <Button
        variant="ghost"
        className="mb-6"
        onClick={() => router.push("/lesson-plans")}
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Kembali ke Daftar
      </Button>

      <LessonPlanEditor plan={plan} onUpdate={(updated) => setPlan(updated)} />
    </div>
  );
}
