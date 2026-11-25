using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Hooks
{
	/// <summary>
	/// The tick-skipping behind <see cref="SlowMotion"/>.
	/// <para>Why this lives in Core/Hooks: tModLoader has no public hook that skips a vanilla entity's whole update
	/// (<c>PreAI</c> skips the AI but not the movement, the frame, the buffs or the timers), so this detours the six vanilla
	/// methods that <c>Main.DoUpdateInWorld</c> calls per entity each tick (decompiled): <c>Player.Update</c>,
	/// <c>NPC.UpdateNPC</c>, <c>Projectile.Update</c>, <c>Item.UpdateItem</c>, <c>Gore.Update</c> and the static
	/// <c>Dust.UpdateDust</c>. Each detour calls the original unless a slow motion holds this entity back this tick (the
	/// world-wide one, or a zone round its centre: <see cref="SlowMotion.ShouldUpdate"/>), so with none running they cost one
	/// bool test per entity (D1). If the detours can't be applied (a tModLoader update renamed a method), one error is logged
	/// and slow motion is simply off: nothing ever freezes (D0 rule 14). tModLoader removes <c>On_</c> detours itself when the
	/// mod unloads.</para>
	/// </summary>
	public sealed class SlowMotionHooks : ModSystem
	{
		public static bool Loaded { get; private set; }

		public override void Load() {
			try {
				On_Player.Update += SkipPlayer;
				On_NPC.UpdateNPC += SkipNPC;
				On_Projectile.Update += SkipProjectile;
				On_Item.UpdateItem += SkipItem;
				On_Gore.Update += SkipGore;
				On_Dust.UpdateDust += SkipDust;
				Loaded = true;
			}
			catch (Exception e) {
				Loaded = false;
				SafeLog.Error("Hooks.SlowMotion", e);
			}
		}

		public override void Unload() {
			Loaded = false;
		}

		private static void SkipPlayer(On_Player.orig_Update orig, Player self, int i) {
			if (SlowMotion.ShouldUpdate(self.Center)) {
				orig(self, i);
			}
		}

		private static void SkipNPC(On_NPC.orig_UpdateNPC orig, NPC self, int i) {
			if (SlowMotion.ShouldUpdate(self.Center)) {
				orig(self, i);
			}
		}

		private static void SkipProjectile(On_Projectile.orig_Update orig, Projectile self, int i) {
			if (CogpunkSets.IgnoresSlowMotionType(self.type) || SlowMotion.ShouldUpdate(self.Center)) {
				orig(self, i);
			}
		}

		private static void SkipItem(On_Item.orig_UpdateItem orig, Item self, int i) {
			if (SlowMotion.ShouldUpdate(self.Center)) {
				orig(self, i);
			}
		}

		private static void SkipGore(On_Gore.orig_Update orig, Gore self) {
			if (SlowMotion.ShouldUpdate(self.position)) {
				orig(self);
			}
		}

		private static void SkipDust(On_Dust.orig_UpdateDust orig) {
			if (SlowMotion.DustShouldUpdate()) {
				orig();
			}
		}
	}
}
