"""
Main Canvas Dashboard for Phase 2 - Step A: Multiverse Foundation.
Minimal CLI to verify WorldState, Snapshots, and Branching.
"""
import os
import sys
from typing import Dict, List, Any

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.history_manager import HistoryManager
from v2_core.stream_engine import StreamEngine
from v2_core.variant_engine import VariantEngine
from v2_core.archive_engine import ArchiveEngine
from v2_core.clustering_engine import ClusteringEngine
from v2_core.ai_stream_engine import AIStreamEngine
from v2_core.ai_alias_engine import AIAliasEngine
from v2_core.scene_beat_engine import SceneBeatEngine
from v2_core.chronology_engine import ChronologyEngine
from v2_core.taste_engine import TasteEngine
from v2_core.convergence_engine import ConvergenceEngine
from v2_core.acceleration_engine import AccelerationEngine
from v2_core.temptation_engine import PrescriptionEngine

class CanvasDashboard:
    def __init__(self):
        self.history = HistoryManager()
        self.chronology = ChronologyEngine()
        self.state = WorldState()
        self.current_page_idx = 0 # Currently viewed stream page
        self._load_latest()

    def _load_latest(self):
        """Initial load from the current branch's latest state."""
        loaded_state = self.history.switch_branch(self.history.current_branch_id)
        if loaded_state:
            self.state = loaded_state
            self.current_page_idx = max(0, len(self.state.stream_pages) - 1)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def draw_header(self):
        mode_str = "FINAL_MODE" if self.state.finalize_mode else "INFINITE_MODE"
        print("=" * 60)
        print(f" [ Infinite Narrative Canvas - {mode_str} ] ")
        print("=" * 60)

    def show_narrative_profile(self):
        """Top Zone 2: Narrative Gravity Summary (Finalize Mode focus)."""
        # Re-compute profile periodically
        profile = ConvergenceEngine.compute_narrative_vector(self.state)
        print(f"[ 0. NARRATIVE PROFILE ]")
        logline = f"'{profile.get('core_theme')}' 테마가 '{profile.get('core_tone')}'의 톤으로 응축되고 있습니다."
        print(f" LOGLINE   : {logline}")
        print(f" Dom Tags  : {', '.join(profile.get('dominant_tags', []))}")
        print(f" Core Nodes: {len(self.state.committed_core['cards'])} Cards, {len(self.state.committed_core['groups'])} Groups")
        print("-" * 60)

    def show_momentum_panel(self):
        """Top Zone 3: Narrative Momentum & Sync (Phase 7)."""
        m = self.state.momentum_level
        s = self.state.sync_intensity
        
        # ASCII Bar for Momentum
        bar_len = 20
        m_fill = min(bar_len, int(m * 5))
        m_bar = "█" * m_fill + "░" * (bar_len - m_fill)
        
        print(f"[ MOMENTUM ] [{m_bar}] {m:.1f}x Speed")
        print(f"[ RESONANCE] Sync Intensity: {s*100:.1f}%")
        if self.state.stagnation_score > 3:
            print(f" ! WARNING : Narrative stagnation detected ({self.state.stagnation_score})")
        print("-" * 60)

    def show_diagnosis_report(self):
        """Top Zone 4: Dr. AI Narrative Health (Phase 7.1)."""
        ailment = self.state.narrative_ailment
        side_effects = self.state.side_effect_count
        
        heartbeat = "♥───♥───♥" if ailment == "HEALTHY" else "⚡─↯─⚡─↯─⚡"
        print(f"[ Dr. AI DIAGNOSIS ] {heartbeat}")
        print(f" Status: {ailment}")
        print(f" Risk  : Side Effect Accumulation ({side_effects})")
        print("-" * 60)

    def show_decision_panel(self):
        """Zone for Urgent Decisions in Finalize Mode."""
        ConvergenceEngine.classify_narrative_layers(self.state)
        print(f"\n[ 1. CRITICAL DECISION PANEL ]")
        cands = self.state.commit_candidates["cards"]
        if not cands:
            print(" (No urgent candidates. Generate more beats to see convergence.)")
        else:
            print(f" [SUGGESTED COMMIT] {len(cands)} pieces waiting for your seal.")
            for i, c in enumerate(cands[:3]): # Top 3 only for speed
                print(f"  > {c['card']['name']} (Score: {ConvergenceEngine.get_narrative_score(c['card'], self.state)['score']:.2f}) - {c['reason']}")
        print("-" * 60)

    def show_world_summary(self):
        """Top Zone: WorldState Summary."""
        print(f"\n[ 1. CURRENT WORLDSTATE SUMMARY ]")
        print(f"- Active Branch : {self.history.current_branch_id}")
        print(f"- Timeline Mode : {self.state.timeline_mode}")
        print(f"- Canvas Cards  : {len(self.state.active_canvas_cards)}")
        print(f"- Stream Pages  : {len(self.state.stream_pages)} (View: Page {self.current_page_idx + 1})")
        print(f"- Archive Cards : {len(self.state.archive_cards)} (Fav: {len(self.state.favorite_cards)})")
        print("-" * 60)

    def show_branch_list(self):
        """Middle Zone: Branch Metadata List."""
        print(f"\n[ 2. AVAILABLE BRANCHES ]")
        branches = self.history.list_branches()
        for bid, meta in branches.items():
            current_tag = "[ACTIVE] " if bid == self.history.current_branch_id else "         "
            name = meta.get("name", "Unnamed")
            snaps_count = len(meta.get("snapshots", []))
            
            # Get latest snapshot summary if available
            last_summary = "No snapshots"
            if snaps_count > 0:
                last_snap_id = meta["snapshots"][-1]
                last_snap = self.history.load_snapshot(last_snap_id)
                if last_snap:
                    last_summary = last_snap.get("metadata", {}).get("summary", "No summary")
            
            print(f"{current_tag}ID: {bid} | Name: {name} ({snaps_count} snaps)")
            print(f"           > Latest: {last_summary}")
        print("-" * 60)

    def show_stream_viewer(self):
        """Middle Zone 2: Stream Paging Viewer."""
        print(f"\n[ 3. CARD STREAM VIEWER ]")
        if not self.state.stream_pages:
            print(" (No stream pages. Use 'M' to generate more inspiration.)")
        else:
            page = self.state.stream_pages[self.current_page_idx]
            print(f" Showing Page {self.current_page_idx + 1} of {len(self.state.stream_pages)}")
            for i, card in enumerate(page):
                print(f"  {i+1}. [{card.get('category')}] {card.get('name')} (ID: {card.get('cid', 'None')})")
        print("-" * 60)

    def show_groups_and_archive(self):
        """Bottom Zone 2: Groups and Archive Statistics."""
        print(f"\n[ 4. GROUPS & ARCHIVE ]")
        # Groups
        if not self.state.card_groups:
            print(" Groups : (No clusters created yet. Use 'G' to group cards.)")
        else:
            print(f" Groups : {len(self.state.card_groups)} clusters active.")
            for group in self.state.card_groups[:3]: # Show up to 3
                print(f"  - {group['name']} ({len(group['card_ids'])} cards) | Alias: {group['alias_suggestion']}")
        
        # Archive
        stats = ArchiveEngine.get_archive_stats(self.state)
        print(f" Archive: {stats['compressed_pages']} pages compressed into metadata.")
        print("-" * 60)

    def show_commit_and_prune(self):
        """Zone for Recommendations in Finalize Mode."""
        ConvergenceEngine.classify_narrative_layers(self.state)
        print(f"\n[ 7. CONVERGENCE RECOMMENDATIONS ]")
        
        c = self.state.commit_candidates["cards"]
        p = self.state.prune_candidates["cards"]
        
        if not c and not p:
            print(" (Data points insufficient for convergence suggestions.)")
        else:
            if c:
                print(f" [!] Commit Suggestion: {len(c)} cards align perfectly with your core.")
                print(f"     Recommend: '{c[0]['card']['name']}' - {c[0]['reason']}")
            if p:
                print(f" [?] Pruning Suggestion: {len(p)} cards are drifting away from the theme.")
        print("-" * 60)

    def show_taste_dashboard(self):
        """Bottom Zone 4: Evolutionary Taste Persona."""
        print(f"\n[ 6. EVOLUTIONARY TASTE ]")
        hot_picks = TasteEngine.get_hot_picks(self.state)
        persona = TasteEngine.get_evolutionary_context(self.state)
        
        print(f" Hot Picks : {', '.join(hot_picks) if hot_picks else '(No recent data)'}")
        print(f" Persona   :\n{persona}")
        print("-" * 60)

    def show_latest_beat(self):
        """Bottom Zone 3: Recent Narrative Output."""
        if not self.state.story_beats:
            return
            
        print(f"\n[ 5. RECENT SCENE BEAT ]")
        last_beat = self.state.story_beats[-1]
        print(f" Beat : {last_beat.get('beat_text')}")
        print(f" Memo : {last_beat.get('directing_memo')}")
        print(f" Next : {last_beat.get('next_inspiration')}")
        print("-" * 60)

    def run(self):
        while True:
            self.clear_screen()
            self.draw_header()
            if self.state.finalize_mode:
                self.show_narrative_profile()
                self.show_decision_panel()
            
            self.show_momentum_panel()
            self.show_diagnosis_report()
            self.show_world_summary()
            self.show_branch_list()
            self.show_stream_viewer()
            
            if not self.state.finalize_mode:
                self.show_groups_and_archive()
                self.show_taste_dashboard()
            
            self.show_latest_beat()
            
            print(f"\n[ COMMANDS ]")
            if not self.state.finalize_mode:
                print(" (S)ave Snapshot | (B)ranch Creation | (W)itch Branch | (M)ore / (A)I Stream")
                print(" ( [ ) Prev Page | ( ] ) Next Page   | (V)ariant Gen  | (G)roup Cards")
                print(" (N)ext Beat     | (H) Alias Hint    | (K)ommit Log   | (F)inalize Mode | (Q)uit")
            else:
                print(" (F) / ( [ ) / ( ] ) Navigation | (O) Profile View | (J) Commit Cand | (P) Prune Cand")
                print(" (X) Export Final    | (S)ave Snapshot | (Q)uit")
                
            cmd = input("\nSelect Action: ").strip().lower()

            if cmd == 'q':
                break
            elif cmd == 's':
                summary = input("Enter Snapshot Summary: ")
                # Update dummy state for demo
                self.state.metadata["total_scenes"] += 1
                self.history.save_snapshot(self.state, summary=summary)
                print("\nSnapshot saved successfully!")
                input("Press Enter to continue...")
            elif cmd == 'b':
                branches = self.history.list_branches()
                current_snaps = branches[self.history.current_branch_id]["snapshots"]
                if not current_snaps:
                    print("\nError: Create at least one snapshot before branching.")
                    input("Press Enter to continue...")
                    continue
                
                name = input("Enter New Branch Name: ")
                new_bid = self.history.create_branch(current_snaps[-1], branch_name=name)
                print(f"\nBranch '{name}' created from {current_snaps[-1]}!")
                input("Press Enter to continue...")
            elif cmd == 'w':
                self.show_branch_list()
                target_bid = input("Enter Branch ID to switch: ").strip()
                # Update Taste on Switch
                TasteEngine.apply_decay(self.state)
                
                if target_bid in self.history.branches:
                    # Multiverse Briefing
                    print("\n" + "=" * 40)
                    print(self.history.get_branch_briefing(target_bid))
                    print("=" * 40)
                    input("Press Enter to begin transition...")
                    
                    self.history.switch_branch(target_bid)
                    self._load_latest()
                    print(f"\nTimeline shifted to Branch {target_bid}.")
                else:
                    print(f"\nError: Branch {target_bid} not found.")
                input("Press Enter to continue...")
            elif cmd == 'm':
                print("\nGenerating new stream page...")
                new_page = StreamEngine.generate_stream_page(count=10)
                StreamEngine.append_stream_page(self.state, new_page)
                self.current_page_idx = len(self.state.stream_pages) - 1
                print("New page added to the multiverse stream.")
                input("Press Enter to continue...")
            elif cmd == '[':
                self.current_page_idx = max(0, self.current_page_idx - 1)
            elif cmd == ']':
                self.current_page_idx = min(len(self.state.stream_pages) - 1, self.current_page_idx + 1)
            elif cmd == 'v':
                if not self.state.stream_pages:
                    print("\nError: No stream cards available to transform.")
                else:
                    page = self.state.stream_pages[self.current_page_idx]
                    idx = int(input(f"Enter card number (1-{len(page)}) to transform to FUTURE: ")) - 1
                    original_card = page[idx]
                    variant = VariantEngine.create_variant_card(original_card, timeline="FUTURE")
                    
                    # Store variant in archive for now to prove it works
                    self.state.archive_cards.append(variant)
                    print(f"\nVariant created! Origin: {original_card['cid']} -> New: {variant['cid']}")
                    print(f"Variant Name: {variant['name']}")
                input("Press Enter to continue...")
                input("Press Enter to continue...")
            elif cmd == 'c':
                num = ArchiveEngine.compress_old_stream_pages(self.state, keep_recent=10)
                print(f"\nSuccessfully compressed {num} old pages into metadata.")
                self.current_page_idx = max(0, len(self.state.stream_pages) - 1)
                input("Press Enter to continue...")
            elif cmd == 'g':
                if not self.state.stream_pages:
                    print("\nError: No cards available to group.")
                else:
                    page = self.state.stream_pages[self.current_page_idx]
                    indices_raw = input(f"Enter card numbers to group (e.g. 1 3 5): ").split()
                    selected_cards = []
                    try:
                        for idx_str in indices_raw:
                            idx = int(idx_str) - 1
                            selected_cards.append(page[idx])
                        
                        new_group = ClusteringEngine.create_group(selected_cards)
                        ClusteringEngine.add_group_to_state(self.state, new_group)
                        print(f"\nCreated {new_group['name']} with {len(selected_cards)} cards!")
                    except Exception as e:
                        print(f"\nError creating group: {e}")
                input("Press Enter to continue...")
                input("Press Enter to continue...")
            elif cmd == 'a':
                print("\nAI is dreaming of your world...")
                new_page = AIStreamEngine.generate_ai_stream_page(self.state, count=10)
                StreamEngine.append_stream_page(self.state, new_page)
                self.current_page_idx = len(self.state.stream_pages) - 1
                print("New AI inspiration page added to the stream.")
                input("Press Enter to continue...")
            elif cmd == 'h':
                if not self.state.card_groups:
                    print("\nError: Create a group (G) first to get AI alias suggestions.")
                else:
                    g_idx = int(input(f"Select group number (1-{len(self.state.card_groups)}): ")) - 1
                    group = self.state.card_groups[g_idx]
                    print(f"\nAI is interpreting Group: {group['name']}...")
                    aliases = AIAliasEngine.suggest_group_alias(group, self.state)
                    for i, suggestion in enumerate(aliases.get("suggestions", [])):
                        print(f"  {i+1}. [{suggestion['name']}] : {suggestion['reason']}")
                input("Press Enter to continue...")
            elif cmd == 'n':
                print(f"\nGenerating narrative beat for timeline: {self.state.timeline_mode}...")
                beat = SceneBeatEngine.generate_scene_beat(self.state)
                self.state.story_beats.append(beat)
                print("Scene beat manifested in the current reality.")
                input("Press Enter to continue...")
            elif cmd == 'f':
                self.state.finalize_mode = not self.state.finalize_mode
                print(f"\nFinalize Mode {'ENABLED' if self.state.finalize_mode else 'DISABLED'}")
                input("Press Enter to continue...")
            elif cmd == 'o':
                profile = ConvergenceEngine.compute_narrative_vector(self.state)
                print("\n[ NARRATIVE GRAVITY REPORT ]")
                import json
                print(json.dumps(profile, indent=2, ensure_ascii=False))
                input("Press Enter to continue...")
            elif cmd == 'j':
                print("\n[ COMMIT CANDIDATES ]")
                cands = self.state.commit_candidates["cards"]
                if not cands:
                    print("No strong candidates for commitment yet.")
                else:
                    for i, c in enumerate(cands):
                        print(f" {i+1}. {c['card']['name']} (Score: 0.8+) - {c['reason']}")
                    sel = input("\nEnter number to commit as CORE, or (A)ll, or (C)ancel: ").strip().lower()
                    if sel == 'a':
                        for c in cands: self.state.committed_core["cards"].append(c["card"])
                        print("All candidates committed to core.")
                    elif sel.isdigit():
                        idx = int(sel) - 1
                        self.state.committed_core["cards"].append(cands[idx]["card"])
                        print(f"'{cands[idx]['card']['name']}' committed.")
                input("Press Enter to continue...")
            elif cmd == 'p':
                print("\n[ PRUNE CANDIDATES ]")
                cands = self.state.prune_candidates["cards"]
                if not cands:
                    print("No elements identified for pruning.")
                else:
                    for i, c in enumerate(cands):
                        print(f" {i+1}. {c['card']['name']} - {c['reason']}")
                    print("\n(Note: Pruning will move these to 'prune_candidate' layer in next update.)")
                input("Press Enter to continue...")
            elif cmd == 'x':
                print("\nCreating Final Chronicle from Committed Core...")
                # Also commit current latest beats if any
                if self.state.story_beats:
                    for beat in self.state.story_beats:
                        self.state.committed_core["beats"].append(beat)
                
                path = self.chronology.export_final_chronicle(self.state)
                print(f"FINAL WORK EXPORTED: {path}")
                input("Press Enter to continue...")
            elif cmd == 'k':
                if not self.state.story_beats:
                    print("\nError: No scene beats available to commit.")
                else:
                    print("\nSynthesizing narrative logic from current beats...")
                    summary = self.chronology.summarize_beats(self.state.story_beats)
                    
                    # Update HistoryManager
                    branch_id = self.history.current_branch_id
                    self.history.add_to_branch_history(branch_id, summary)
                    
                    # Export Markdown
                    branch_name = self.history.branches[branch_id]["name"]
                    log = self.history.branches[branch_id].get("narrative_log", [])
                    file_path = self.chronology.export_chronicle_md(self.state, branch_name, log)
                    
                    # Clear processed beats
                    self.state.story_beats = []
                    # Auto-snapshot on commit
                    self.history.save_snapshot(self.state, f"Committed: {summary[:30]}...")
                    
                    print(f"\nK-COMMIT SUCCESS!")
                    print(f"Summary: {summary}")
                    print(f"Chronicle saved to: {file_path}")
                input("Press Enter to continue...")
            elif cmd == 'p':
                if not self.state.stream_pages:
                    print("\nNo cards available.")
                else:
                    page = self.state.stream_pages[self.current_page_idx]
                    idx = int(input("Pick card number to Canvas: ")) - 1
                    card = page[idx]
                    self.state.active_canvas_cards.append(card)
                    TasteEngine.record_interaction(self.state, card, "PICK")
                    
                    # Phase 7: Luck Card Activation
                    if card.get("category") == "LUCK":
                        if "Prescription" in card.get("tags", []):
                            print(f"\n[RX] INJECTING TREATMENT: {card['name']}...")
                            result = PrescriptionEngine.process_treatment(self.state, card)
                            print(f"\n[RESULT] {result['message']}")
                            
                            if result["status"] == "FAILURE":
                                # Create Failure Branch!
                                snap_id = self.history.save_snapshot(self.state, summary="Failure: Side Effect Event")
                                b_id = self.history.create_branch(snap_id, branch_name=f"SIDE_EFFECT_{card['cid']}")
                                print(f"\n[!] Reality Stabilizers failing. Forced transition to Branch {b_id}.")
                                input("Press Enter to stabilize...")
                                self.history.switch_branch(b_id)
                                self._load_latest()
                        else:
                            print(f"\n[!] LUCK CARD ACTIVATED: {card['name']}")
                            AccelerationEngine.trigger_surge(self.state, card.get("luck_type", "NITRO_SWIFT"))
                    else:
                        # Normal pick maintains momentum
                        self.state.momentum_level = min(5.0, self.state.momentum_level + 0.1)
                        AccelerationEngine.update_stagnation(self.state, action_taken=True)
                        
                    print(f"\nCard '{card['name']}' added to Canvas.")
                input("Press Enter to continue...")
            elif cmd == 'f':
                if not self.state.stream_pages:
                    print("\nNo cards available.")
                else:
                    page = self.state.stream_pages[self.current_page_idx]
                    idx = int(input("Favorite card number: ")) - 1
                    card = page[idx]
                    self.state.favorite_cards.append(card)
                    TasteEngine.record_interaction(self.state, card, "FAVORITE")
                    print(f"\nCard '{card['name']}' favorited.")
                input("Press Enter to continue...")
            elif cmd == 'd':
                if not self.state.stream_pages:
                    print("\nNo cards available.")
                else:
                    page = self.state.stream_pages[self.current_page_idx]
                    idx = int(input("Discard card number: ")) - 1
                    card = page[idx]
                    self.state.discarded_cards.append(card)
                    TasteEngine.record_interaction(self.state, card, "DISCARD")
                    print(f"\nCard '{card['name']}' discarded. (Avoidance pressure applied)")
                input("Press Enter to continue...")
            elif cmd == 'r':
                print("\n[ DEEP INSPECTION ]")
                import json
                print(json.dumps(self.state.to_dict(), indent=2, ensure_ascii=False))
                input("Press Enter to continue...")

if __name__ == "__main__":
    dashboard = CanvasDashboard()
    dashboard.run()
