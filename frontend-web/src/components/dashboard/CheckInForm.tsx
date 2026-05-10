import { useMemo } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Send } from "lucide-react";

import { api } from "@/api/client";
import type { ActivityLevel, CheckInResponse } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/api/client";

/* -------------------------------------------------------------------------
 * Schema — mirrors `backend/schemas.py::CheckInRequest`.
 * Validation lives client-side via zod and server-side via Pydantic; the
 * server is the source of truth, but client validation keeps the form
 * snappy and surface error states early.
 * ----------------------------------------------------------------------- */

const ACTIVITY_LEVELS: { value: ActivityLevel; label: string }[] = [
  { value: "sedentary", label: "Sedentary" },
  { value: "light", label: "Light" },
  { value: "moderate", label: "Moderate" },
  { value: "active", label: "Active" },
];

const checkInSchema = z.object({
  user_id: z
    .string()
    .min(1, "Required")
    .max(64, "Up to 64 characters")
    .trim(),
  sleep_hours: z.number().min(0).max(12),
  mood_score: z.number().int().min(1).max(10),
  activity_level: z.enum(["sedentary", "light", "moderate", "active"]),
  social_interactions: z.number().int().min(0).max(30),
  journal_text: z
    .string()
    .max(5000, "Keep it under 5,000 characters")
    .optional()
    .or(z.literal("")),
});

type CheckInFormValues = z.infer<typeof checkInSchema>;

interface CheckInFormProps {
  defaultUserId?: string;
  onSuccess?: (result: CheckInResponse) => void;
}

export function CheckInForm({ defaultUserId, onSuccess }: CheckInFormProps) {
  const queryClient = useQueryClient();

  const defaults = useMemo<CheckInFormValues>(
    () => ({
      user_id: defaultUserId ?? "",
      sleep_hours: 7,
      mood_score: 7,
      activity_level: "moderate",
      social_interactions: 3,
      journal_text: "",
    }),
    [defaultUserId],
  );

  const {
    control,
    handleSubmit,
    register,
    watch,
    formState: { errors },
    reset,
  } = useForm<CheckInFormValues>({
    resolver: zodResolver(checkInSchema),
    defaultValues: defaults,
  });

  const mutation = useMutation({
    mutationFn: (values: CheckInFormValues) =>
      api.submitCheckIn({
        ...values,
        journal_text:
          values.journal_text && values.journal_text.length > 0
            ? values.journal_text
            : null,
      }),
    onSuccess: (data) => {
      // Refresh history / trends / stats for this user.
      queryClient.invalidateQueries({ queryKey: ["history", data.user_id] });
      queryClient.invalidateQueries({ queryKey: ["trend", data.user_id] });
      queryClient.invalidateQueries({ queryKey: ["stats", data.user_id] });
      reset({ ...defaults, user_id: data.user_id, journal_text: "" });
      onSuccess?.(data);
    },
  });

  const moodValue = watch("mood_score");
  const sleepValue = watch("sleep_hours");
  const socialValue = watch("social_interactions");
  const activityValue = watch("activity_level");

  const errorMessage = (() => {
    if (!mutation.isError) return null;
    const e = mutation.error;
    if (e instanceof ApiError) return e.message;
    return e instanceof Error ? e.message : "Something went wrong.";
  })();

  return (
    <Card>
      <CardContent className="p-7">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-display text-lg font-semibold">
              Daily check-in
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Takes under a minute. Your data is stored locally; we never echo
              crisis language back to you.
            </p>
          </div>
        </div>

        <form
          onSubmit={handleSubmit((values) => mutation.mutate(values))}
          className="mt-7 space-y-6"
          noValidate
        >
          {/* User ID */}
          <div className="space-y-2">
            <Label htmlFor="user_id">User ID</Label>
            <Input
              id="user_id"
              placeholder="user_001"
              autoComplete="off"
              spellCheck={false}
              {...register("user_id")}
            />
            {errors.user_id && (
              <p className="text-xs text-brand-rose">
                {errors.user_id.message}
              </p>
            )}
          </div>

          {/* Sleep slider 0..12 */}
          <Controller
            control={control}
            name="sleep_hours"
            render={({ field }) => (
              <div className="space-y-3">
                <div className="flex items-baseline justify-between">
                  <Label htmlFor="sleep_hours">Sleep last night</Label>
                  <span className="font-display text-sm font-semibold text-brand-cyan">
                    {sleepValue.toFixed(1)} hr
                  </span>
                </div>
                <Slider
                  id="sleep_hours"
                  min={0}
                  max={12}
                  step={0.5}
                  value={[field.value]}
                  onValueChange={(v) => field.onChange(v[0])}
                />
              </div>
            )}
          />

          {/* Mood slider 1..10 */}
          <Controller
            control={control}
            name="mood_score"
            render={({ field }) => (
              <div className="space-y-3">
                <div className="flex items-baseline justify-between">
                  <Label htmlFor="mood_score">Mood (1 = low · 10 = great)</Label>
                  <span className="font-display text-sm font-semibold text-brand-cyan">
                    {moodValue} / 10
                  </span>
                </div>
                <Slider
                  id="mood_score"
                  min={1}
                  max={10}
                  step={1}
                  value={[field.value]}
                  onValueChange={(v) => field.onChange(Math.round(v[0]))}
                />
              </div>
            )}
          />

          {/* Activity level — segmented */}
          <Controller
            control={control}
            name="activity_level"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Activity level</Label>
                <div
                  role="radiogroup"
                  aria-label="Activity level"
                  className="grid grid-cols-2 gap-2 sm:grid-cols-4"
                >
                  {ACTIVITY_LEVELS.map((opt) => {
                    const active = activityValue === opt.value;
                    return (
                      <button
                        type="button"
                        key={opt.value}
                        role="radio"
                        aria-checked={active}
                        onClick={() => field.onChange(opt.value)}
                        className={
                          active
                            ? "h-11 rounded-xl bg-grad-brand text-sm font-semibold text-white shadow-[0_10px_25px_-15px_rgba(99,102,241,0.7)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                            : "h-11 rounded-xl border border-white/10 bg-white/[0.04] text-sm font-medium text-muted-foreground transition-colors hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                        }
                      >
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          />

          {/* Social interactions — slider 0..30 */}
          <Controller
            control={control}
            name="social_interactions"
            render={({ field }) => (
              <div className="space-y-3">
                <div className="flex items-baseline justify-between">
                  <Label htmlFor="social_interactions">
                    Meaningful social contacts today
                  </Label>
                  <span className="font-display text-sm font-semibold text-brand-cyan">
                    {socialValue}
                  </span>
                </div>
                <Slider
                  id="social_interactions"
                  min={0}
                  max={30}
                  step={1}
                  value={[field.value]}
                  onValueChange={(v) => field.onChange(Math.round(v[0]))}
                />
              </div>
            )}
          />

          {/* Journal text */}
          <div className="space-y-2">
            <Label htmlFor="journal_text">
              Journal{" "}
              <span className="font-normal text-muted-foreground">
                · optional
              </span>
            </Label>
            <Textarea
              id="journal_text"
              placeholder="How are you feeling today? Anything on your mind…"
              rows={5}
              {...register("journal_text")}
            />
            {errors.journal_text && (
              <p className="text-xs text-brand-rose">
                {errors.journal_text.message}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              Empty journals are fine — risk weights re-normalise so you're
              not under-scored.
            </p>
          </div>

          {/* Submit + status */}
          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" size="lg" disabled={mutation.isPending}>
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Submitting…
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  Submit check-in
                </>
              )}
            </Button>
            {errorMessage && (
              <span className="text-sm text-brand-rose">{errorMessage}</span>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
