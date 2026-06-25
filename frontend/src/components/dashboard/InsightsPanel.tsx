import { useState } from "react";
import { useIntentMutation, useAffectMutation, useDrift, useConflictMutation } from "@/hooks/use-api";
import { driftChartUrl } from "@/lib/api";
import { Loader2 } from "lucide-react";

export function InsightsPanel() {
  const [intentText, setIntentText] = useState("");
  const intentMutation = useIntentMutation();

  const [affectText, setAffectText] = useState("");
  const affectMutation = useAffectMutation();

  const [driftView, setDriftView] = useState<"real" | "demo">("demo");
  const { data: driftData, isLoading: driftLoading } = useDrift(driftView);

  const [conflictQuery, setConflictQuery] = useState("");
  const conflictMutation = useConflictMutation();

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 w-full max-w-5xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold readable-text mb-2">Backend Insights</h1>
        <p className="readable-muted text-sm">Direct access to the Round 2 machine learning pipelines.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Intent Classifier */}
        <section className="glass rounded-2xl p-6 flex flex-col gap-4">
          <div>
            <h2 className="readable-text text-base font-semibold">Intent Classifier</h2>
            <p className="readable-muted text-xs mt-1">Enter a query to see its routed intent label.</p>
          </div>
          
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              if (intentText.trim()) intentMutation.mutate({ text: intentText });
            }}
            className="flex items-center gap-2"
          >
            <input
              value={intentText}
              onChange={(e) => setIntentText(e.target.value)}
              placeholder="e.g., Remind me to buy milk"
              className="glass-strong flex-1 rounded-lg px-4 py-2 text-sm outline-none placeholder:text-[#B7BBC6] disabled:opacity-50"
              disabled={intentMutation.isPending}
            />
            <button
              type="submit"
              disabled={!intentText.trim() || intentMutation.isPending}
              className="rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-40"
              style={{ background: "var(--color-accent)", color: "var(--color-text-primary)" }}
            >
              {intentMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : "Classify"}
            </button>
          </form>

          {intentMutation.data && (
            <div className="mt-2 flex items-center gap-6 glass-strong rounded-xl p-4">
              <div>
                <div className="readable-muted text-[11px] uppercase tracking-wider font-semibold mb-2">Label</div>
                {intentMutation.data.label === "unknown" ? (
                  <span className="readable-muted text-sm capitalize">{intentMutation.data.label}</span>
                ) : (
                  <span className="glass-pill rounded-full px-3 py-1 text-xs font-medium" style={{ color: "var(--color-success)", borderColor: "var(--color-success)" }}>
                    {intentMutation.data.label}
                  </span>
                )}
              </div>
              <div>
                <div className="readable-muted text-[11px] uppercase tracking-wider font-semibold mb-2">Confidence</div>
                <div className="font-mono text-lg readable-text">{(intentMutation.data.confidence * 100).toFixed(1)}%</div>
              </div>
            </div>
          )}
        </section>

        {/* Affect Meter */}
        <section className="glass rounded-2xl p-6 flex flex-col gap-4">
          <div>
            <h2 className="readable-text text-base font-semibold">Affect Engine (Lexicon)</h2>
            <p className="readable-muted text-xs mt-1">Analyze the emotional axes of a text snippet.</p>
          </div>

          <form 
            onSubmit={(e) => {
              e.preventDefault();
              if (affectText.trim()) affectMutation.mutate({ text: affectText });
            }}
            className="flex items-center gap-2"
          >
            <input
              value={affectText}
              onChange={(e) => setAffectText(e.target.value)}
              placeholder="e.g., I'm incredibly frustrated by this!"
              className="glass-strong flex-1 rounded-lg px-4 py-2 text-sm outline-none placeholder:text-[#B7BBC6] disabled:opacity-50"
              disabled={affectMutation.isPending}
            />
            <button
              type="submit"
              disabled={!affectText.trim() || affectMutation.isPending}
              className="rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-40"
              style={{ background: "var(--color-accent)", color: "var(--color-text-primary)" }}
            >
              {affectMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : "Score"}
            </button>
          </form>

          {affectMutation.data && (
            <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-4 glass-strong rounded-xl p-4">
              {Object.entries(affectMutation.data).map(([key, val]) => {
                let colorVar = "var(--color-accent)";
                if (key === "frustration") colorVar = "var(--color-danger)";
                else if (key === "playfulness") colorVar = "var(--color-success)";
                else if (key === "curiosity") colorVar = "var(--color-accent)";
                else if (key === "formality" || key === "intensity") colorVar = "var(--color-text-muted)";
                
                let width = `${Math.min(100, Math.max(0, val * 100))}%`;
                let left = "0%";

                if (key === "valence") {
                  if (val > 0) {
                    colorVar = "var(--color-success)";
                    width = `${Math.min(50, val * 50)}%`;
                    left = "50%";
                  } else if (val < 0) {
                    colorVar = "var(--color-danger)";
                    const w = Math.min(50, Math.abs(val) * 50);
                    width = `${w}%`;
                    left = `${50 - w}%`;
                  } else {
                    colorVar = "var(--color-text-muted)";
                    width = "4px";
                    left = "calc(50% - 2px)";
                  }
                }

                return (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="readable-muted capitalize">{key}</span>
                      <span className="font-mono readable-text">{val.toFixed(2)}</span>
                    </div>
                    <div className="relative h-1.5 w-full overflow-hidden rounded-full" style={{ background: "var(--color-bg-tertiary)" }}>
                      <div 
                        className="absolute top-0 bottom-0 rounded-full transition-all duration-300" 
                        style={{ background: colorVar, width, left }}
                      />
                      {key === "valence" && (
                        <div className="absolute top-0 bottom-0 w-px bg-white/20" style={{ left: "50%" }} />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Drift Viewer */}
        <section className="glass rounded-2xl p-6 flex flex-col gap-4 lg:col-span-2">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="readable-text text-base font-semibold">Drift Timeline</h2>
              <p className="readable-muted text-xs mt-1">Analyze emotional shifts and topic triggers over time.</p>
            </div>
            
            <div className="inline-flex items-center rounded-full border p-0.5" style={{ borderColor: "rgba(255,255,255,0.12)", background: "rgba(12,12,16,0.72)", backdropFilter: "blur(14px)" }}>
              {(["demo", "real"] as const).map((view) => {
                const isActive = driftView === view;
                return (
                  <button
                    key={view}
                    onClick={() => setDriftView(view)}
                    className="rounded-full px-4 py-1 text-xs font-medium transition-colors duration-150"
                    style={{
                      background: isActive ? "var(--color-text-primary)" : "transparent",
                      color: isActive ? "var(--color-bg-primary)" : "var(--color-text-secondary)",
                    }}
                  >
                    {view === "demo" ? "Demo Arc" : "Real Export"}
                  </button>
                );
              })}
            </div>
          </div>

          {driftView === "real" && (
            <div className="rounded-xl border p-4" style={{ borderColor: "rgba(245,158,11,0.2)", background: "rgba(245,158,11,0.05)" }}>
              <div className="mb-1 text-[13px] font-semibold" style={{ color: "var(--color-warning)" }}>
                ⚠️ Data Caveat
              </div>
              <div className="readable-muted text-[12px] leading-relaxed">
                The original PersonaChat dataset consists of disconnected daily chats with different people. Treating it as continuous history causes massive emotional whiplash. The Drift engine is designed to run on true, long-term continuous logs.
              </div>
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-2 mt-2">
            <div className="glass-strong rounded-xl p-4 flex items-center justify-center min-h-[300px]">
              <img 
                src={driftChartUrl(driftView)} 
                alt="Drift Chart" 
                className="max-w-full rounded-md object-contain mix-blend-screen"
                style={{ filter: "invert(0.9) hue-rotate(180deg) saturate(1.5) contrast(1.1)" }}
                key={driftChartUrl(driftView)}
              />
            </div>
            
            <div className="glass-strong rounded-xl overflow-hidden flex flex-col">
              <div className="overflow-x-auto flex-1 max-h-[350px]">
                <table className="w-full text-left text-sm">
                  <thead className="sticky top-0 bg-black/50 backdrop-blur-md">
                    <tr>
                      <th className="px-4 py-3 readable-muted font-medium border-b" style={{ borderColor: "var(--color-border)" }}>Day Range</th>
                      <th className="px-4 py-3 readable-muted font-medium border-b" style={{ borderColor: "var(--color-border)" }}>Tone</th>
                      <th className="px-4 py-3 readable-muted font-medium border-b" style={{ borderColor: "var(--color-border)" }}>Mood</th>
                      <th className="px-4 py-3 readable-muted font-medium border-b" style={{ borderColor: "var(--color-border)" }}>Trigger</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y" style={{ borderColor: "var(--color-border)" }}>
                    {driftLoading ? (
                      <tr>
                        <td colSpan={4} className="p-4">
                          <div className="flex flex-col gap-2">
                            {Array.from({ length: 4 }).map((_, i) => (
                              <div key={i} className="shimmer h-10 w-full rounded-md" />
                            ))}
                          </div>
                        </td>
                      </tr>
                    ) : driftData?.segments?.length ? (
                      driftData.segments.map((s, i) => (
                        <tr key={i} className="transition-colors hover:bg-white/5">
                          <td className="px-4 py-3 font-mono readable-text text-xs whitespace-nowrap">{s.day_range}</td>
                          <td className="px-4 py-3 readable-text text-xs">{s.dominant_tone}</td>
                          <td className="px-4 py-3">
                            <span className="glass-pill rounded-full px-2 py-1 text-[11px] whitespace-nowrap">{s.dominant_mood}</span>
                          </td>
                          <td className="px-4 py-3 readable-muted text-[11px] leading-relaxed">
                            {s.detected_trigger ? (
                              <div className="flex flex-col gap-1">
                                {s.detected_trigger.keyword_spike && (
                                  <div><span className="opacity-50">Spike:</span> {s.detected_trigger.keyword_spike}</div>
                                )}
                                {s.detected_trigger.new_entity && (
                                  <div><span className="opacity-50">Entity:</span> {s.detected_trigger.new_entity}</div>
                                )}
                                {s.detected_trigger.new_topic && (
                                  <div className="line-clamp-2" title={s.detected_trigger.new_topic}>
                                    <span className="opacity-50">Topic:</span> {s.detected_trigger.new_topic}
                                  </div>
                                )}
                              </div>
                            ) : "-"}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center readable-muted">
                          No data available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* Conflict Resolver */}
        <section className="glass rounded-2xl p-6 flex flex-col gap-4 lg:col-span-2">
          <div>
            <h2 className="readable-text text-base font-semibold">RAG Conflict Resolver</h2>
            <p className="readable-muted text-xs mt-1">Reconciles historical contradictions in retrieved context using emotional polarity and NLI.</p>
          </div>

          <form 
            onSubmit={(e) => {
              e.preventDefault();
              if (conflictQuery.trim()) conflictMutation.mutate({ query: conflictQuery });
            }}
            className="flex items-center gap-2 max-w-2xl"
          >
            <input
              value={conflictQuery}
              onChange={(e) => setConflictQuery(e.target.value)}
              placeholder="e.g., how do I feel about my sister?"
              className="glass-strong flex-1 rounded-lg px-4 py-2 text-sm outline-none placeholder:text-[#B7BBC6] disabled:opacity-50"
              disabled={conflictMutation.isPending}
            />
            <button
              type="submit"
              disabled={!conflictQuery.trim() || conflictMutation.isPending}
              className="rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-40"
              style={{ background: "var(--color-accent)", color: "var(--color-text-primary)" }}
            >
              {conflictMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : "Resolve"}
            </button>
          </form>

          {conflictMutation.data && (
            <div className="mt-4 grid gap-6 lg:grid-cols-2">
              <div className="flex flex-col gap-4">
                <div>
                  <div className="readable-muted text-[11px] uppercase tracking-wider font-semibold mb-2">Subject Extracted</div>
                  <span className="glass-pill rounded-full px-3 py-1 text-xs">{conflictMutation.data.subject || "None"}</span>
                </div>
                
                <div>
                  <div className="readable-muted text-[11px] uppercase tracking-wider font-semibold mb-2">Resolution</div>
                  <div className="glass-strong rounded-xl p-5 readable-text text-sm leading-relaxed border-l-4" style={{ borderLeftColor: "var(--color-accent)" }}>
                    {conflictMutation.data.resolution.merged_answer}
                  </div>
                </div>

                {(conflictMutation.data.resolution.emotional_contradiction || 
                  (conflictMutation.data.resolution.factual_contradictions?.length ?? 0) > 0) ? (
                  <div className="rounded-xl border p-4" style={{ borderColor: "rgba(239,68,68,0.2)", background: "rgba(239,68,68,0.05)" }}>
                    <div className="mb-2 text-[13px] font-semibold" style={{ color: "var(--color-danger)" }}>
                      ⚠️ Contradictions Detected
                    </div>
                    <ul className="list-disc pl-5 space-y-1 readable-muted text-[13px]">
                      {conflictMutation.data.resolution.emotional_contradiction && (
                        <li>Emotional polarity shift detected over time.</li>
                      )}
                      {conflictMutation.data.resolution.factual_contradictions?.map((f: any, i: number) => (
                        <li key={i}>{f[0]} vs {f[1]}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="rounded-xl border p-4" style={{ borderColor: "rgba(16,185,129,0.2)", background: "rgba(16,185,129,0.05)" }}>
                    <div className="text-[13px] font-semibold" style={{ color: "var(--color-success)" }}>
                      ✓ No contradiction / consistent
                    </div>
                  </div>
                )}
              </div>

              <div>
                <div className="readable-muted text-[11px] uppercase tracking-wider font-semibold mb-3">Context Timeline</div>
                
                <div className="flex flex-col gap-2 max-h-[400px] overflow-y-auto pr-2">
                  {conflictMutation.data.before.map((b: any, i: number) => (
                    <div key={`b-${i}`} className="glass rounded-xl p-3">
                      <span className="font-mono text-[10px] readable-muted mr-2">Day {b.day}</span>
                      <span className="readable-muted text-[13px]">{b.text}</span>
                    </div>
                  ))}
                  {conflictMutation.data.after.map((a: any, i: number) => (
                    <div key={`a-${i}`} className="rounded-xl p-3 border" style={{ borderColor: "rgba(16,185,129,0.2)", background: "rgba(16,185,129,0.05)" }}>
                      <span className="font-mono text-[10px] mr-2" style={{ color: "var(--color-success)" }}>Day {a.day}</span>
                      <span className="readable-text text-[13px]">{a.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>

      </div>
    </div>
  );
}
