import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Badge } from "../ui/badge";
import { Loader2, AlertCircle } from "lucide-react";

export function CheckInForm({ onSubmissionSuccess }: { onSubmissionSuccess?: () => void }) {
  const [userId, setUserId] = useState("user_001");
  const [sleepHours, setSleepHours] = useState([7]);
  const [moodScore, setMoodScore] = useState([6]);
  const [activityLevel, setActivityLevel] = useState("moderate");
  const [socialInteractions, setSocialInteractions] = useState("3");
  const [journalText, setJournalText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/checkin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          sleep_hours: sleepHours[0],
          mood_score: moodScore[0],
          activity_level: activityLevel,
          social_interactions: parseInt(socialInteractions),
          journal_text: journalText || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      if (onSubmissionSuccess) onSubmissionSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to submit check-in");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Daily Check-in</CardTitle>
          <CardDescription>
            How are you feeling today? Your data helps Sentinel identify early signals.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="user-id">User ID</Label>
                <Input
                  id="user-id"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="user_001"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="activity">Activity Level</Label>
                <select
                  id="activity"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={activityLevel}
                  onChange={(e) => setActivityLevel(e.target.value)}
                >
                  <option value="sedentary">Sedentary</option>
                  <option value="light">Light</option>
                  <option value="moderate">Moderate</option>
                  <option value="active">Active</option>
                </select>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Sleep Hours</Label>
                  <span className="text-sm font-medium text-muted-foreground">{sleepHours[0]}h</span>
                </div>
                <input
                  type="range"
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-brand-cyan"
                  value={sleepHours[0]}
                  onChange={(e) => setSleepHours([parseFloat(e.target.value)])}
                  min="0"
                  max="12"
                  step="0.5"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Mood Score (1-10)</Label>
                  <span className="text-sm font-medium text-muted-foreground">{moodScore[0]}</span>
                </div>
                <input
                  type="range"
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-brand-indigo"
                  value={moodScore[0]}
                  onChange={(e) => setMoodScore([parseInt(e.target.value)])}
                  min="1"
                  max="10"
                  step="1"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="social">Social Interactions</Label>
              <Input
                id="social"
                type="number"
                value={socialInteractions}
                onChange={(e) => setSocialInteractions(e.target.value)}
                min="0"
                max="50"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="journal">Journal Entry (Optional)</Label>
              <Textarea
                id="journal"
                placeholder="Write about your day, feelings, or anything on your mind..."
                value={journalText}
                onChange={(e) => setJournalText(e.target.value)}
                rows={4}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                "Submit Check-in"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="flex items-center gap-3 p-4 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p className="text-sm font-medium">{error}</p>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card className={`border-2 ${
          result.risk_level === 'HIGH' ? 'border-brand-rose' : 
          result.risk_level === 'MEDIUM' ? 'border-brand-amber' : 'border-brand-teal'
        }`}>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Risk Assessment
              <Badge className={
                result.risk_level === 'HIGH' ? 'bg-brand-rose' : 
                result.risk_level === 'MEDIUM' ? 'bg-brand-amber' : 'bg-brand-teal'
              }>
                {result.risk_level} Risk
              </Badge>
            </CardTitle>
            <CardDescription>
              Based on your {result.days_tracked}-day history and current signals.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm italic leading-relaxed">
                "{result.recommendation}"
              </p>
            </div>

            {result.safety_override && (
              <div className="rounded-lg bg-brand-rose/20 p-4 border border-brand-rose/50">
                <div className="flex items-center gap-2 text-brand-rose font-bold mb-2">
                  <AlertCircle className="h-5 w-5" />
                  Safety Notice
                </div>
                <p className="text-xs text-brand-rose/90">
                  Our NLP system detected phrases associated with self-harm or crisis. 
                  Please use the crisis resources listed in the sidebar or footer immediately.
                </p>
              </div>
            )}

            <div className="grid gap-4 grid-cols-2 text-center sm:grid-cols-4">
              <div>
                <div className="text-xs text-muted-foreground uppercase font-semibold">Risk Score</div>
                <div className="text-xl font-bold">{(result.risk_score * 100).toFixed(0)}%</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase font-semibold">Anomaly</div>
                <div className="text-xl font-bold">{result.anomaly_detected ? "Yes" : "No"}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase font-semibold">Sentiment</div>
                <div className="text-xl font-bold capitalize">{result.nlp_analysis?.sentiment_label || "N/A"}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase font-semibold">Dominant</div>
                <div className="text-xl font-bold truncate">{result.dominant_factor || "None"}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
