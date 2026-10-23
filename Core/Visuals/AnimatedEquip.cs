using System;
using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Visuals
{
	/// <summary>
	/// Armor pieces whose equip texture animates on its own clock (spinning cogs, pistons, gauges).
	/// <para>Vanilla draws an armor piece from one equip texture per slot and picks the frame inside it from the player's
	/// body animation, so a texture can't animate by itself. <see cref="Register"/> adds one more equip texture per
	/// animation frame (<c>{Texture}_{Type}_{n}.png</c>, n = 1..frames-1; frame 0 is the normal <c>[AutoloadEquip]</c>
	/// texture) and <see cref="AnimatedEquipPlayer"/> swaps the visible slot to the current frame.</para>
	/// <para>Why this hook (decompiled tModLoader v2026.08.3.0): <c>Player.PlayerFrame</c> resets head/body/legs from the
	/// armor and vanity slots every tick, then calls <c>ModPlayer.FrameEffects</c> before anything is drawn. Only our own
	/// base slot is replaced, so vanity, costumes and other mods keep priority, and vanilla's draw layers render the frame:
	/// positioning, head bob, dyes, afterimages, invisibility and mounts are unchanged. While the game is paused or the
	/// player is frozen, webbed or stoned, <c>PlayerFrame</c> returns before that hook and the piece shows frame 0.</para>
	/// <para>Frames are registered with their item (like ExampleMod's ExampleCostume), so every frame slot maps back to it
	/// for vanity sets and <c>EquipTexture</c> hooks. They're registered in <c>Load()</c>, which <c>ModType</c> runs before
	/// <c>Register()</c> adds the <c>[AutoloadEquip]</c> texture, so the item keeps its base slot.</para>
	/// <para>The clock is <see cref="Main.timeForVisualEffects"/>, which advances every update (menus included) on every
	/// client, so all pieces and all players stay in step with nothing to sync. Dedicated servers register nothing.</para>
	/// </summary>
	public sealed class AnimatedEquip : ModSystem
	{
		public const int MaxFrames = 16;

		private sealed class Entry
		{
			public ModItem Item;
			public EquipType Type;
			public int TicksPerFrame;
			public int BaseSlot = -1;
			public int[] Slots;       // [0] = base slot, [n] = frame n (the base slot if that frame failed to load)
		}

		private static readonly List<Entry> pending = new();
		private static Entry[] entries = Array.Empty<Entry>();

		internal static bool Any => entries.Length > 0;

		/// <summary>
		/// Call from the armor item's <c>Load()</c>. <paramref name="frames"/> includes frame 0 (the autoloaded texture);
		/// a missing frame texture is logged once and shows frame 0 instead.
		/// </summary>
		public static void Register(ModItem item, EquipType type, int frames, int ticksPerFrame) {
			if (Main.dedServ || item == null || frames < 2) {
				return;
			}
			if (type != EquipType.Head && type != EquipType.Body && type != EquipType.Legs) {
				SafeLog.Warn("AnimatedEquip.Type:" + item.Name, "{0}: only head, body and legs textures can be animated.", item.Name);
				return;
			}
			Entry entry = new() {
				Item = item,
				Type = type,
				TicksPerFrame = Math.Max(1, ticksPerFrame),
				Slots = new int[Math.Min(frames, MaxFrames)],
			};
			for (int n = 1; n < entry.Slots.Length; n++) {
				entry.Slots[n] = -1;
				string texture = $"{item.Texture}_{type}_{n}";
				if (!ModContent.HasAsset(texture)) {
					SafeLog.Warn("AnimatedEquip.Missing:" + texture, "Missing equip frame '{0}'; that frame shows frame 0.", texture);
					continue;
				}
				try {
					entry.Slots[n] = EquipLoader.AddEquipTexture(item.Mod, texture, type, item, $"{item.Name}_Frame{n}");
				}
				catch (Exception e) {   // load-time boundary: lose the frame, not the mod
					SafeLog.Warn("AnimatedEquip.Load:" + texture, "Equip frame '{0}' failed to load: {1}", texture, e.Message);
				}
			}
			pending.Add(entry);
		}

		public override void PostSetupContent() {
			List<Entry> resolved = new(pending.Count);
			foreach (Entry entry in pending) {
				entry.BaseSlot = EquipLoader.GetEquipSlot(entry.Item.Mod, entry.Item.Name, entry.Type);
				if (entry.BaseSlot <= 0) {
					SafeLog.Warn("AnimatedEquip.NoBase:" + entry.Item.Name, "{0} has no autoloaded equip texture to animate.", entry.Item.Name);
					continue;
				}
				entry.Slots[0] = entry.BaseSlot;
				for (int n = 1; n < entry.Slots.Length; n++) {
					if (entry.Slots[n] <= 0) {
						entry.Slots[n] = entry.BaseSlot;
					}
					else {
						CopyFlags(entry.Type, entry.BaseSlot, entry.Slots[n]);
					}
				}
				resolved.Add(entry);
			}
			entries = resolved.ToArray();
			pending.Clear();
		}

		public override void Unload() {
			pending.Clear();
			entries = Array.Empty<Entry>();
		}

		/// <summary>The slot to draw this tick for a visible slot. Allocation-free; called from FrameEffects.</summary>
		internal static int Animate(EquipType type, int slot) {
			if (slot <= 0) {
				return slot;
			}
			Entry[] list = entries;
			for (int i = 0; i < list.Length; i++) {
				Entry entry = list[i];
				if (entry.BaseSlot == slot && entry.Type == type) {
					int frame = (int)(Main.timeForVisualEffects / entry.TicksPerFrame) % entry.Slots.Length;
					return entry.Slots[frame];
				}
			}
			return slot;
		}

		// Draw flags an item sets for its own slot in SetStaticDefaults (hair, skin, hands...) must hold for every frame,
		// or the head would flash hair or the hands would blink between frames.
		private static void CopyFlags(EquipType type, int from, int to) {
			switch (type) {
				case EquipType.Head:
					Copy(ArmorIDs.Head.Sets.DrawHead, from, to);
					Copy(ArmorIDs.Head.Sets.DrawFullHair, from, to);
					Copy(ArmorIDs.Head.Sets.DrawHatHair, from, to);
					Copy(ArmorIDs.Head.Sets.DrawsBackHairWithoutHeadgear, from, to);
					Copy(ArmorIDs.Head.Sets.IsTallHat, from, to);
					Copy(ArmorIDs.Head.Sets.UseSkinColor, from, to);
					Copy(ArmorIDs.Head.Sets.PreventBeardDraw, from, to);
					Copy(ArmorIDs.Head.Sets.UseAltFaceHeadDraw, from, to);
					Copy(ArmorIDs.Head.Sets.FrontToBackID, from, to);
					break;
				case EquipType.Body:
					Copy(ArmorIDs.Body.Sets.HidesTopSkin, from, to);
					Copy(ArmorIDs.Body.Sets.HidesBottomSkin, from, to);
					Copy(ArmorIDs.Body.Sets.HidesHands, from, to);
					Copy(ArmorIDs.Body.Sets.HidesArms, from, to);
					Copy(ArmorIDs.Body.Sets.NeedsToDrawArm, from, to);
					Copy(ArmorIDs.Body.Sets.showsShouldersWhileJumping, from, to);
					Copy(ArmorIDs.Body.Sets.shouldersAreAlwaysInTheBack, from, to);
					Copy(ArmorIDs.Body.Sets.DisableHandOnAndOffAccDraw, from, to);
					Copy(ArmorIDs.Body.Sets.DisableBeltAccDraw, from, to);
					Copy(ArmorIDs.Body.Sets.IncludedCapeBack, from, to);
					Copy(ArmorIDs.Body.Sets.IncludedCapeBackFemale, from, to);
					Copy(ArmorIDs.Body.Sets.IncludedCapeFront, from, to);
					break;
				case EquipType.Legs:
					Copy(ArmorIDs.Legs.Sets.HidesTopSkin, from, to);
					Copy(ArmorIDs.Legs.Sets.HidesBottomSkin, from, to);
					Copy(ArmorIDs.Legs.Sets.OverridesLegs, from, to);
					Copy(ArmorIDs.Legs.Sets.IncompatibleWithFrogLeg, from, to);
					break;
			}
		}

		private static void Copy<T>(T[] set, int from, int to) {
			if (set != null && from >= 0 && to >= 0 && from < set.Length && to < set.Length) {
				set[to] = set[from];
			}
		}
	}

	/// <summary>Swaps each visible animated armor slot to its current frame; see <see cref="AnimatedEquip"/>.</summary>
	public sealed class AnimatedEquipPlayer : ModPlayer
	{
		public override void FrameEffects() {
			if (!AnimatedEquip.Any) {
				return;
			}
			Player.head = AnimatedEquip.Animate(EquipType.Head, Player.head);
			Player.body = AnimatedEquip.Animate(EquipType.Body, Player.body);
			Player.legs = AnimatedEquip.Animate(EquipType.Legs, Player.legs);
		}
	}
}
