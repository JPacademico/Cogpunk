using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Visuals
{
	/// <summary>
	/// The drawn half of a smooth slow motion (user, 2026-11-26: "be more smooth so they dont feel like a shutter"). A held
	/// entity only updates every few ticks (<see cref="SlowMotion"/>), so drawn as it is it stands still and then jumps a whole
	/// step: a shutter. Here, just before each frame is drawn (vanilla's <c>Main.OnPreDraw</c>, which runs before the camera is
	/// placed, decompiled <c>Main.DoDraw</c>), every held entity is moved on by the share of its last step that has passed since
	/// it updated (<see cref="SlowMotion.HeldFraction"/>), so it glides at its slowed speed; the camera follows the gliding
	/// player. Right after the frame (<c>Main.OnPostDraw</c>) each is put back exactly where it was, before anything updates or
	/// is sent (and again at the start of the next update, should a frame ever end without it).
	/// <para>The step: for players, NPCs and projectiles, how far the entity moved in its last update (noted by
	/// <see cref="Hooks.SlowMotionHooks"/>, so a held weapon rides with its holder); for items, gore and dust, their velocity.
	/// A step longer than <see cref="MaxStep"/> (a teleport) glides nowhere, and a step from an earlier slow motion is never
	/// used. A player's held item moves with them.</para>
	/// <para>D0: clients only (the server draws nothing); nothing but positions is touched, each put back to the exact value it
	/// had (or, if something moved it while drawing, by the same amount); the buffers are fixed and allocated once (D1); the
	/// handlers are removed on unload (D0 rule 12). D2: purely visual: no entity is ever updated, synced or tested where it
	/// was drawn.</para>
	/// </summary>
	public sealed class SlowMotionSmoothing : ModSystem
	{
		public const float MaxStep = 96f;

		private enum Kind : byte { Player, NPC, Projectile, Item, Gore, Dust }

		private static Vector2[] playerStep, npcStep, projectileStep;
		private static int[] playerEpisode, npcEpisode, projectileEpisode;

		// the entities moved for this frame
		private static Kind[] kinds;
		private static int[] indices;
		private static Vector2[] originals, written, shifts;
		private static Vector2[] heldOriginals, heldWritten;              // a player's held item (itemLocation)
		private static int count;
		private static bool hooked;

		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			playerStep = new Vector2[Main.player.Length];
			npcStep = new Vector2[Main.npc.Length];
			projectileStep = new Vector2[Main.projectile.Length];
			playerEpisode = new int[Main.player.Length];
			npcEpisode = new int[Main.npc.Length];
			projectileEpisode = new int[Main.projectile.Length];
			int capacity = Main.player.Length + Main.npc.Length + Main.projectile.Length + Main.item.Length + Main.gore.Length + Main.dust.Length;
			kinds = new Kind[capacity];
			indices = new int[capacity];
			originals = new Vector2[capacity];
			written = new Vector2[capacity];
			shifts = new Vector2[capacity];
			heldOriginals = new Vector2[capacity];
			heldWritten = new Vector2[capacity];
			count = 0;
			try {
				Main.OnPreDraw += Glide;
				Main.OnPostDraw += PutBack;
				hooked = true;
			}
			catch (Exception e) {
				hooked = false;
				SafeLog.Error("Visuals.SlowMotionSmoothing", e);
			}
		}

		public override void Unload() {
			if (hooked) {
				Main.OnPreDraw -= Glide;
				Main.OnPostDraw -= PutBack;
				hooked = false;
			}
			if (count > 0) {
				Restore();
			}
			playerStep = npcStep = projectileStep = null;
			playerEpisode = npcEpisode = projectileEpisode = null;
			kinds = null;
			indices = null;
			originals = written = shifts = heldOriginals = heldWritten = null;
			count = 0;
		}

		// --- the steps (the hooks, on each update while a slow motion runs) ---------------------------------------------------

		public static void NotePlayer(int i, Vector2 step) => Note(playerStep, playerEpisode, i, step);

		public static void NoteNPC(int i, Vector2 step) => Note(npcStep, npcEpisode, i, step);

		public static void NoteProjectile(int i, Vector2 step) => Note(projectileStep, projectileEpisode, i, step);

		private static void Note(Vector2[] steps, int[] episodes, int i, Vector2 step) {
			if (steps == null || i < 0 || i >= steps.Length) {
				return;
			}
			steps[i] = step;
			episodes[i] = SlowMotion.Episode;
		}

		private static Vector2 StepOf(Vector2[] steps, int[] episodes, int i) {
			if (steps == null || i < 0 || i >= steps.Length || episodes[i] != SlowMotion.Episode) {
				return Vector2.Zero;                                    // nothing noted in this slow motion yet
			}
			return steps[i];
		}

		// --- the glide ----------------------------------------------------------------------------------------------------------

		private static void Glide(GameTime _) {
			if (count > 0) {
				Restore();                                              // never moved twice
			}
			if (Main.gameMenu || !SlowMotion.AnyActive || kinds == null) {
				return;
			}
			for (int i = 0; i < Main.maxPlayers && i < Main.player.Length; i++) {
				Player p = Main.player[i];
				if (p == null || !p.active || p.dead) {
					continue;
				}
				Vector2 shift = ShiftFor(p.Center, StepOf(playerStep, playerEpisode, i));
				if (shift != Vector2.Zero && count < kinds.Length) {
					heldOriginals[count] = p.itemLocation;
					p.itemLocation += shift;
					heldWritten[count] = p.itemLocation;
					Push(Kind.Player, i, ref p.position, shift);
				}
			}
			for (int i = 0; i < Main.maxNPCs && i < Main.npc.Length; i++) {
				NPC n = Main.npc[i];
				if (n == null || !n.active) {
					continue;
				}
				Vector2 shift = ShiftFor(n.Center, StepOf(npcStep, npcEpisode, i));
				if (shift != Vector2.Zero) {
					Push(Kind.NPC, i, ref n.position, shift);
				}
			}
			for (int i = 0; i < Main.maxProjectiles && i < Main.projectile.Length; i++) {
				Projectile p = Main.projectile[i];
				if (p == null || !p.active || CogpunkSets.IgnoresSlowMotionType(p.type)) {
					continue;
				}
				Vector2 shift = ShiftFor(p.Center, StepOf(projectileStep, projectileEpisode, i));
				if (shift != Vector2.Zero) {
					Push(Kind.Projectile, i, ref p.position, shift);
				}
			}
			for (int i = 0; i < Main.maxItems && i < Main.item.Length; i++) {
				Item it = Main.item[i];
				if (it == null || !it.active) {
					continue;
				}
				Vector2 shift = ShiftFor(it.Center, it.velocity);
				if (shift != Vector2.Zero) {
					Push(Kind.Item, i, ref it.position, shift);
				}
			}
			for (int i = 0; i < Main.gore.Length; i++) {
				Gore g = Main.gore[i];
				if (g == null || !g.active) {
					continue;
				}
				Vector2 shift = ShiftFor(g.position, g.velocity);
				if (shift != Vector2.Zero) {
					Push(Kind.Gore, i, ref g.position, shift);
				}
			}
			if (!SlowMotion.ZonesActive && !SlowMotion.Active) {
				return;
			}
			float dustShare = SlowMotion.HeldFraction(SlowMotion.ViewCenter);  // dust follows the zone round the view
			if (dustShare <= 0f) {
				return;
			}
			for (int i = 0; i < Main.dust.Length; i++) {
				Dust d = Main.dust[i];
				if (d == null || !d.active) {
					continue;
				}
				Vector2 step = d.velocity;
				if (step.LengthSquared() > MaxStep * MaxStep || !MathSafety.IsFinite(step)) {
					continue;
				}
				Vector2 shift = step * dustShare;
				if (shift != Vector2.Zero) {
					Push(Kind.Dust, i, ref d.position, shift);
				}
			}
		}

		/// <summary>The glide of an entity at <paramref name="at"/> whose last step was <paramref name="step"/> (zero when it isn't
		/// held, the step is a teleport or isn't finite).</summary>
		private static Vector2 ShiftFor(Vector2 at, Vector2 step) {
			if (step == Vector2.Zero || step.LengthSquared() > MaxStep * MaxStep || !MathSafety.IsFinite(step)) {
				return Vector2.Zero;
			}
			float share = SlowMotion.HeldFraction(at);
			return share > 0f ? step * share : Vector2.Zero;
		}

		private static void Push(Kind kind, int index, ref Vector2 position, Vector2 shift) {
			if (count >= kinds.Length) {
				return;
			}
			kinds[count] = kind;
			indices[count] = index;
			originals[count] = position;
			shifts[count] = shift;
			position += shift;
			written[count] = position;
			count++;
		}

		private static void PutBack(GameTime _) {
			if (count > 0) {
				Restore();
			}
		}

		/// <summary>Should a frame ever end without <see cref="PutBack"/>, the entities go back before anything updates.</summary>
		public override void PreUpdateEntities() {
			if (count > 0) {
				Restore();
			}
		}

		/// <summary>Every moved entity back: to the exact value it had, or (if something moved it while drawing) by the shift.</summary>
		private static void Restore() {
			for (int k = count - 1; k >= 0; k--) {
				int i = indices[k];
				switch (kinds[k]) {
					case Kind.Player:
						if (i < Main.player.Length && Main.player[i] != null) {
							Back(ref Main.player[i].position, k);
							Player p = Main.player[i];
							p.itemLocation = p.itemLocation == heldWritten[k] ? heldOriginals[k] : p.itemLocation - shifts[k];
						}
						break;
					case Kind.NPC:
						if (i < Main.npc.Length && Main.npc[i] != null) {
							Back(ref Main.npc[i].position, k);
						}
						break;
					case Kind.Projectile:
						if (i < Main.projectile.Length && Main.projectile[i] != null) {
							Back(ref Main.projectile[i].position, k);
						}
						break;
					case Kind.Item:
						if (i < Main.item.Length && Main.item[i] != null) {
							Back(ref Main.item[i].position, k);
						}
						break;
					case Kind.Gore:
						if (i < Main.gore.Length && Main.gore[i] != null) {
							Back(ref Main.gore[i].position, k);
						}
						break;
					default:
						if (i < Main.dust.Length && Main.dust[i] != null) {
							Back(ref Main.dust[i].position, k);
						}
						break;
				}
			}
			count = 0;
		}

		private static void Back(ref Vector2 position, int k) {
			position = position == written[k] ? originals[k] : position - shifts[k];
		}
	}
}
