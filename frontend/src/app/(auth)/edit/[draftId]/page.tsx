'use client';

import { useEffect, useState } from 'react';
import {
  Loader2, Trash2, Wand2, Scissors, Volume2, VolumeX, Type, Download, Sparkles,
  Smile, ArrowUp, ArrowDown, Mic, Music,
} from 'lucide-react';
import { editorApi, aiApi, uploadApi, type EditorState, type Segment, type Sticker, type SoundRecommendation, type FilterPreset, type AIAgent, type AgentExecution } from '@/lib/api';

interface EditPageProps {
  params: { draftId: string };
}

const VOICES = [
  { id: 'en-US-female-1', label: 'English (US) — Female' },
  { id: 'en-US-male-1', label: 'English (US) — Male' },
  { id: 'en-GB-female-1', label: 'English (UK) — Female' },
  { id: 'es-ES-female-1', label: 'Spanish — Female' },
];

const EFFECTS = ['blur', 'brighten', 'saturate', 'desaturate', 'vintage', 'cinematic'];

export default function EditPage({ params }: EditPageProps) {
  const [state, setState] = useState<EditorState | null>(null);
  const [stickersBySegment, setStickersBySegment] = useState<Record<string, Sticker[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [busySegmentId, setBusySegmentId] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await editorApi.getEditorState(params.draftId);
      setState(data);

      const entries = await Promise.all(
        data.segments.map(async (segment) => {
          const { stickers } = await editorApi.getStickers(segment.id);
          return [segment.id, stickers] as const;
        })
      );
      setStickersBySegment(Object.fromEntries(entries));

      const draft = await uploadApi.getDraft(params.draftId);
      if (draft.music_id) setSelectedSoundId(draft.music_id);
    } catch {
      setError('Failed to load editor state');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.draftId]);

  useEffect(() => {
    aiApi.getFilterPresets().then(setFilterPresets).catch(() => {});
    aiApi.getAgents().then(setAgents).catch(() => {});
  }, []);

  const updateSegment = (updated: Segment) => {
    setState((prev) =>
      prev
        ? { ...prev, segments: prev.segments.map((s) => (s.id === updated.id ? updated : s)) }
        : prev
    );
  };

  const withBusy = async (segmentId: string, action: () => Promise<Segment>) => {
    setBusySegmentId(segmentId);
    try {
      const updated = await action();
      updateSegment(updated);
    } catch {
      setError('Action failed');
    } finally {
      setBusySegmentId(null);
    }
  };

  const handleApplyEffect = (segmentId: string, effect: string) =>
    withBusy(segmentId, () => editorApi.applyEffect(segmentId, effect));

  const handleSpeedChange = (segmentId: string, speed: number) =>
    withBusy(segmentId, () => editorApi.adjustSpeed(segmentId, speed));

  const handleVolumeChange = (segmentId: string, volume: number) =>
    withBusy(segmentId, () => editorApi.adjustVolume(segmentId, volume));

  const handleToggleMute = (segment: Segment) =>
    withBusy(segment.id, () => editorApi.muteSegment(segment.id, !segment.muted));

  const handleDeleteSegment = async (segmentId: string) => {
    setBusySegmentId(segmentId);
    try {
      await editorApi.deleteSegment(segmentId);
      setState((prev) =>
        prev ? { ...prev, segments: prev.segments.filter((s) => s.id !== segmentId) } : prev
      );
    } catch {
      setError('Failed to delete segment');
    } finally {
      setBusySegmentId(null);
    }
  };

  const handleAddTextOverlay = async (segmentId: string) => {
    const text = window.prompt('Overlay text');
    if (!text) return;
    try {
      await editorApi.addTextOverlay(segmentId, { text, x: 50, y: 50, width: 200, height: 60 });
      await load();
    } catch {
      setError('Failed to add text overlay');
    }
  };

  const handleAddSticker = async (segmentId: string) => {
    const url = window.prompt('Sticker image URL');
    if (!url) return;
    try {
      await editorApi.addSticker(segmentId, {
        sticker_url: url,
        sticker_type: 'emoji',
        x: 50,
        y: 50,
        width: 100,
        height: 100,
      });
      await load();
    } catch {
      setError('Failed to add sticker');
    }
  };

  const handleDeleteSticker = async (stickerId: string) => {
    try {
      await editorApi.deleteSticker(stickerId);
      await load();
    } catch {
      setError('Failed to delete sticker');
    }
  };

  const handleMoveSegment = async (index: number, direction: -1 | 1) => {
    if (!state) return;
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= state.segments.length) return;

    const reordered = [...state.segments];
    [reordered[index], reordered[newIndex]] = [reordered[newIndex], reordered[index]];
    setState({ ...state, segments: reordered });

    try {
      await editorApi.reorderSegments(params.draftId, reordered.map((s) => s.id));
    } catch {
      setError('Failed to reorder segments');
      await load();
    }
  };

  const [aiStatus, setAiStatus] = useState<Record<string, string>>({});
  const [filterPresets, setFilterPresets] = useState<FilterPreset[]>([]);
  const [appliedFilterBySegment, setAppliedFilterBySegment] = useState<Record<string, string>>({});
  const [agents, setAgents] = useState<AIAgent[]>([]);
  const [runningAgentBySegment, setRunningAgentBySegment] = useState<Record<string, string>>({});
  const [lastExecutionBySegment, setLastExecutionBySegment] = useState<Record<string, AgentExecution>>({});
  const [sounds, setSounds] = useState<SoundRecommendation[]>([]);
  const [soundsLoading, setSoundsLoading] = useState(false);
  const [soundsLoaded, setSoundsLoaded] = useState(false);
  const [selectedSoundId, setSelectedSoundId] = useState<string | null>(null);
  const [soundSaveError, setSoundSaveError] = useState<string | null>(null);

  const handleUseSound = async (soundId: string) => {
    setSoundSaveError(null);
    try {
      const draft = await uploadApi.getDraft(params.draftId);
      await uploadApi.updateDraft(params.draftId, { ...draft, music_id: soundId });
      setSelectedSoundId(soundId);
    } catch {
      setSoundSaveError('Failed to attach sound to this video');
    }
  };

  const handleGenerateVoiceover = async (segmentId: string) => {
    const text = window.prompt('Voiceover script');
    if (!text) return;
    const voiceId = window.prompt(
      `Voice (${VOICES.map((v) => v.id).join(', ')})`,
      VOICES[0].id
    );
    if (!voiceId) return;

    setAiStatus((prev) => ({ ...prev, [segmentId]: 'Generating voiceover... (15 credits)' }));
    try {
      await aiApi.generateVoiceover({ segment_id: segmentId, text, voice_id: voiceId });
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Voiceover queued' }));
    } catch {
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Voiceover generation failed' }));
    }
  };

  const loadSounds = async (category?: string) => {
    setSoundsLoading(true);
    try {
      const result = await aiApi.getSoundRecommendations(category ? { category } : undefined);
      setSounds(result.sounds);
      setSoundsLoaded(true);
    } catch {
      setError('Failed to load sound recommendations');
    } finally {
      setSoundsLoading(false);
    }
  };

  const handleRemoveBackground = async (segmentId: string) => {
    setAiStatus((prev) => ({ ...prev, [segmentId]: 'Removing background... (10 credits)' }));
    try {
      await aiApi.removeBackground({ segment_id: segmentId, mode: 'blur', blur_level: 5 });
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Background removal queued' }));
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Background removal failed';
      setAiStatus((prev) => ({ ...prev, [segmentId]: message }));
    }
  };

  const handleGenerateCaptions = async (segmentId: string) => {
    setAiStatus((prev) => ({ ...prev, [segmentId]: 'Generating captions... (5 credits)' }));
    try {
      await aiApi.generateCaptions({ segment_id: segmentId });
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Captions queued' }));
    } catch {
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Caption generation failed' }));
    }
  };

  const handleApplyFilterPreset = async (segmentId: string, preset: FilterPreset) => {
    setAiStatus((prev) => ({ ...prev, [segmentId]: `Applying ${preset.label}...` }));
    try {
      await aiApi.applyColorCorrection({
        segment_id: segmentId,
        method: 'preset',
        preset_name: preset.name,
        brightness: preset.brightness,
        contrast: preset.contrast,
        saturation: preset.saturation,
        hue: preset.hue,
        temperature: preset.temperature,
      });
      setAppliedFilterBySegment((prev) => ({ ...prev, [segmentId]: preset.name }));
      setAiStatus((prev) => ({ ...prev, [segmentId]: `${preset.label} filter queued` }));
    } catch {
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Failed to apply filter' }));
    }
  };

  const handleRunAgent = async (segmentId: string, agent: AIAgent) => {
    setRunningAgentBySegment((prev) => ({ ...prev, [segmentId]: agent.id }));
    setAiStatus((prev) => ({ ...prev, [segmentId]: `Running ${agent.label}...` }));
    try {
      const execution = await aiApi.executeAgent(agent.id, segmentId);
      setLastExecutionBySegment((prev) => ({ ...prev, [segmentId]: execution }));
      setAiStatus((prev) => ({
        ...prev,
        [segmentId]:
          execution.status === 'completed'
            ? `${agent.label} completed (${execution.total_credits_used} credits)`
            : `${agent.label} failed: ${execution.error_message}`,
      }));
    } catch {
      setAiStatus((prev) => ({ ...prev, [segmentId]: `Failed to run ${agent.label}` }));
    } finally {
      setRunningAgentBySegment((prev) => {
        const next = { ...prev };
        delete next[segmentId];
        return next;
      });
    }
  };

  const handleColorCorrect = async (segmentId: string) => {
    setAiStatus((prev) => ({ ...prev, [segmentId]: 'Applying auto color correction...' }));
    try {
      await aiApi.applyColorCorrection({ segment_id: segmentId, method: 'auto_enhance' });
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Color correction queued' }));
    } catch {
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Color correction failed' }));
    }
  };

  const handleSmartFrame = async (segmentId: string) => {
    setAiStatus((prev) => ({ ...prev, [segmentId]: 'Getting frame suggestions...' }));
    try {
      await aiApi.getFrameSuggestions(segmentId);
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Smart framing queued' }));
    } catch {
      setAiStatus((prev) => ({ ...prev, [segmentId]: 'Smart framing failed' }));
    }
  };

  const handleExport = async () => {
    setExportStatus('Queuing export...');
    try {
      const result = await editorApi.exportVideo(params.draftId);
      setExportStatus(`Export ${result.status} (${result.quality}, ${result.format})`);
    } catch {
      setExportStatus('Export failed');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error && !state) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Edit video</h1>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-6 py-3 bg-pink-600 hover:bg-pink-700 text-white rounded-lg font-semibold"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>

        {exportStatus && (
          <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">{exportStatus}</p>
        )}
        {error && <p className="mb-6 text-sm text-red-600">{error}</p>}

        <p className="text-sm text-gray-500 mb-4">
          Total duration: {((state?.total_duration ?? 0) / 1000).toFixed(1)}s ·{' '}
          {state?.text_overlays.length ?? 0} text overlay(s)
        </p>

        <div className="space-y-4">
          {state?.segments.map((segment, index) => {
            const isBusy = busySegmentId === segment.id;
            return (
              <div
                key={segment.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium">
                    Segment {segment.order + 1} · {segment.content_type}
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleMoveSegment(index, -1)}
                      disabled={isBusy || index === 0}
                      className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30"
                      title="Move up"
                    >
                      <ArrowUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleMoveSegment(index, 1)}
                      disabled={isBusy || index === (state?.segments.length ?? 0) - 1}
                      className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30"
                      title="Move down"
                    >
                      <ArrowDown className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteSegment(segment.id)}
                      disabled={isBusy}
                      className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 p-2 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-3">
                  {EFFECTS.map((effect) => (
                    <button
                      key={effect}
                      onClick={() => handleApplyEffect(segment.id, effect)}
                      disabled={isBusy}
                      className="flex items-center gap-1 px-3 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
                    >
                      <Wand2 className="w-3 h-3" />
                      {effect}
                    </button>
                  ))}
                  {segment.effects?.map((e) => (
                    <span key={e} className="px-3 py-1 text-xs rounded-full bg-pink-100 text-pink-700">
                      {e}
                    </span>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-4 mb-3">
                  <label className="text-xs text-gray-500">
                    Speed
                    <input
                      type="range"
                      min={0.25}
                      max={4}
                      step={0.25}
                      defaultValue={1}
                      disabled={isBusy}
                      onMouseUp={(e) => handleSpeedChange(segment.id, Number((e.target as HTMLInputElement).value))}
                      className="w-full"
                    />
                  </label>
                  <label className="text-xs text-gray-500">
                    Volume ({segment.volume}%)
                    <input
                      type="range"
                      min={0}
                      max={100}
                      defaultValue={segment.volume}
                      disabled={isBusy}
                      onMouseUp={(e) => handleVolumeChange(segment.id, Number((e.target as HTMLInputElement).value))}
                      className="w-full"
                    />
                  </label>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleMute(segment)}
                    disabled={isBusy}
                    className="flex items-center gap-1 px-3 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-800"
                  >
                    {segment.muted ? <VolumeX className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
                    {segment.muted ? 'Unmute' : 'Mute'}
                  </button>
                  <button
                    onClick={() => handleAddTextOverlay(segment.id)}
                    className="flex items-center gap-1 px-3 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-800"
                  >
                    <Type className="w-3 h-3" />
                    Add text
                  </button>
                  <button
                    onClick={() => handleAddSticker(segment.id)}
                    className="flex items-center gap-1 px-3 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-800"
                  >
                    <Smile className="w-3 h-3" />
                    Add sticker
                  </button>
                  <span className="flex items-center gap-1 px-3 py-1 text-xs text-gray-400">
                    <Scissors className="w-3 h-3" />
                    {segment.start_time}ms – {segment.end_time}ms
                  </span>
                </div>

                {(stickersBySegment[segment.id]?.length ?? 0) > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {stickersBySegment[segment.id].map((sticker) => (
                      <span
                        key={sticker.id}
                        className="flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300"
                      >
                        {sticker.sticker_type}
                        <button
                          onClick={() => handleDeleteSticker(sticker.id)}
                          className="hover:text-red-600"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {filterPresets.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                    <p className="text-xs font-semibold text-gray-500 mb-2">Filters</p>
                    <div className="flex flex-wrap gap-2">
                      {filterPresets.map((preset) => {
                        const isApplied = appliedFilterBySegment[segment.id] === preset.name;
                        const previewFilter = `brightness(${1 + preset.brightness / 100}) contrast(${1 + preset.contrast / 100}) saturate(${1 + preset.saturation / 100}) hue-rotate(${preset.hue}deg)`;
                        return (
                          <button
                            key={preset.id}
                            onClick={() => handleApplyFilterPreset(segment.id, preset)}
                            className={`flex flex-col items-center gap-1 px-2 py-1.5 rounded-lg border text-xs ${
                              isApplied
                                ? 'border-pink-600 text-pink-600'
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                            }`}
                          >
                            <span
                              className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-300 to-purple-400"
                              style={{ filter: previewFilter }}
                            />
                            {preset.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> AI tools
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => handleRemoveBackground(segment.id)}
                      className="px-3 py-1 text-xs rounded-full bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 hover:bg-purple-100"
                    >
                      Remove background
                    </button>
                    <button
                      onClick={() => handleGenerateCaptions(segment.id)}
                      className="px-3 py-1 text-xs rounded-full bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 hover:bg-purple-100"
                    >
                      Auto captions
                    </button>
                    <button
                      onClick={() => handleColorCorrect(segment.id)}
                      className="px-3 py-1 text-xs rounded-full bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 hover:bg-purple-100"
                    >
                      Auto color
                    </button>
                    <button
                      onClick={() => handleSmartFrame(segment.id)}
                      className="px-3 py-1 text-xs rounded-full bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 hover:bg-purple-100"
                    >
                      Smart frame
                    </button>
                    <button
                      onClick={() => handleGenerateVoiceover(segment.id)}
                      className="flex items-center gap-1 px-3 py-1 text-xs rounded-full bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 hover:bg-purple-100"
                    >
                      <Mic className="w-3 h-3" />
                      Voiceover
                    </button>
                  </div>

                  {agents.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                      <p className="text-xs font-semibold text-gray-500 mb-2">
                        AI Agents — one-click recipes
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {agents.map((agent) => (
                          <button
                            key={agent.id}
                            title={agent.description || undefined}
                            onClick={() => handleRunAgent(segment.id, agent)}
                            disabled={runningAgentBySegment[segment.id] === agent.id}
                            className="px-3 py-1 text-xs rounded-full bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 disabled:opacity-50"
                          >
                            {runningAgentBySegment[segment.id] === agent.id
                              ? `Running ${agent.label}...`
                              : `Run ${agent.label}`}
                          </button>
                        ))}
                      </div>
                      {lastExecutionBySegment[segment.id] && (
                        <ul className="mt-2 text-xs text-gray-500 space-y-0.5">
                          {lastExecutionBySegment[segment.id].steps_log.map((step, i) => (
                            <li key={i}>
                              {step.status === 'completed' ? '✓' : '✗'} {step.operation}
                              {step.error ? ` — ${step.error}` : ''}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {aiStatus[segment.id] && (
                    <p className="text-xs text-gray-500 mt-2">{aiStatus[segment.id]}</p>
                  )}
                </div>
              </div>
            );
          })}

          {state?.segments.length === 0 && (
            <p className="text-gray-500 text-center py-8">No segments yet</p>
          )}
        </div>

        <section className="mt-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <Music className="w-4 h-4" />
              Sound recommendations
            </h2>
            {!soundsLoaded && (
              <button
                onClick={() => loadSounds()}
                disabled={soundsLoading}
                className="text-sm text-pink-600 hover:underline"
              >
                {soundsLoading ? 'Loading...' : 'Browse sounds'}
              </button>
            )}
          </div>
          {soundsLoaded && (
            <>
              <div className="flex gap-2 mb-4 flex-wrap">
                {['background', 'sound_effect', 'music', 'ambient'].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => loadSounds(cat)}
                    className="px-3 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200"
                  >
                    {cat.replace('_', ' ')}
                  </button>
                ))}
              </div>
              {soundSaveError && (
                <p className="text-xs text-red-600 mb-2">{soundSaveError}</p>
              )}
              {sounds.length === 0 ? (
                <p className="text-sm text-gray-500">No sounds found</p>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {sounds.map((sound) => (
                    <div key={sound.id} className="py-3 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{sound.sound_title}</p>
                        {sound.artist && <p className="text-xs text-gray-500">{sound.artist}</p>}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {sound.is_trending && (
                          <span className="text-xs text-orange-500 font-semibold">Trending</span>
                        )}
                        <button
                          onClick={() => handleUseSound(sound.id)}
                          className={`text-xs px-3 py-1 rounded-full font-semibold transition ${
                            selectedSoundId === sound.id
                              ? 'bg-pink-600 text-white'
                              : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
                          }`}
                        >
                          {selectedSoundId === sound.id ? 'Using' : 'Use this sound'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
