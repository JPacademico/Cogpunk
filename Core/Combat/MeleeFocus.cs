using System;
using System.IO;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Combat
{
	/// <summary>
	/// Whether a player fights in melee: a boss rule (user, 2026-11-09: "if the player that is being targeted is using a
	/// melee armor or melee weapon and the boss is a floaty boss (that stays a certain distance from the target like cursed
	/// conductor) the boss should maintain a melee distance from this player while targeting it (within grass sword
	/// range)"). Read anywhere through <see cref="Of"/>; floaty bosses close in to <see cref="BladeOfGrassReach"/>.
	/// <list type="bullet">
	/// <item><b>A melee weapon</b>: the held item deals melee damage (<c>CountsAsClass(Melee)</c>: swords, spears, yo-yos,
	/// flails, boomerangs...), has damage, and is neither a tool (pickaxe, axe, hammer) nor a whip (whips are summon
	/// weapons, <c>ProjectileID.Sets.IsAWhip</c>).</item>
	/// <item><b>Melee armor</b>: the three worn armor pieces (vanity ignored) give more melee-only bonuses (damage, crit,
	/// attack speed) than any other class's. Each piece type is measured once (<see cref="MeleeGear"/>) with vanilla's own
	/// <c>Player.GrantArmorBenefits</c> on a scratch player flagged as a display doll, which also runs
	/// <c>ModItem.UpdateEquip</c>, so vanilla's and other mods' armor are judged by what they really give. Generic bonuses
	/// count for no class; a melee helmet over generic mail and greaves (the Hardmode ore sets) is melee armor.</item>
	/// </list>
	/// <para>D2: the owning client decides (it alone knows its gear for sure) and sends the verdict to the server when it
	/// changes (<see cref="MeleeFocusPacket"/>, the ModPlayer sync pattern: <c>SyncPlayer</c> + <c>CopyClientState</c> +
	/// <c>SendClientChanges</c>); the server relays it to the other clients. A boss copies its target's verdict into its own
	/// synced state, so every side flies the same path. D0: the measurement runs foreign code on a scratch player, once per
	/// item type, inside a try/catch (a boundary: a piece that throws counts as no class, logged once); every index is
	/// checked. D1: the verdict is a few array reads a tick; nothing allocates after a piece's first measurement.</para>
	/// </summary>
	public sealed class MeleeFocusPlayer : ModPlayer
	{
		/// <summary>True while the player holds a melee weapon or wears melee armor (the owner's verdict, synced).</summary>
		public bool MeleeFocus;

		public override void PostUpdate() {
			if (Player.whoAmI != Main.myPlayer || Main.netMode == NetmodeID.Server) {
				return;
			}
			MeleeFocus = MeleeGear.IsMeleeWeapon(Player.HeldItem) || MeleeGear.WearsMeleeArmor(Player);
		}

		public override void SyncPlayer(int toWho, int fromWho, bool newPlayer) {
			ModContent.GetInstance<MeleeFocusPacket>().Send(Player.whoAmI, MeleeFocus, toWho, fromWho);
		}

		public override void CopyClientState(ModPlayer targetCopy) {
			((MeleeFocusPlayer)targetCopy).MeleeFocus = MeleeFocus;
		}

		public override void SendClientChanges(ModPlayer clientPlayer) {
			if (((MeleeFocusPlayer)clientPlayer).MeleeFocus != MeleeFocus) {
				SyncPlayer(-1, Main.myPlayer, false);
			}
		}
	}

	/// <summary>
	/// The verdict's measurements (see <see cref="MeleeFocusPlayer"/>): per armor item type, its class-only bonuses,
	/// measured on first use and cached for the session.
	/// </summary>
	public sealed class MeleeGear : ModSystem
	{
		/// <summary>The Blade of Grass's reach, game px from the wielder's edge: its 40x40 blade at scale 1 (decompiled 1.4.4
		/// <c>Item.SetDefaults</c> 190) swung from the hand covers about 40 px out in front.</summary>
		public const float BladeOfGrassReach = 40f;

		private const int Classes = 5;                      // melee, ranged, magic, summon, mechanist
		private static float[] scores;                      // [type * Classes + class]
		private static byte[] measured;                     // 0 not yet, 1 measured
		private static Player scratch;
		private static DamageClass mechanist;

		public override void PostSetupContent() {
			scores = new float[ItemLoader.ItemCount * Classes];
			measured = new byte[ItemLoader.ItemCount];
			mechanist = ModContent.TryFind("Cogpunk/MechanistDamage", out DamageClass found) ? found : null;
		}

		public override void Unload() {
			scores = null;
			measured = null;
			scratch = null;
			mechanist = null;
		}

		/// <summary>A melee weapon in hand (see <see cref="MeleeFocusPlayer"/>).</summary>
		public static bool IsMeleeWeapon(Item item) {
			if (item == null || item.IsAir || item.damage <= 0 || item.pick > 0 || item.axe > 0 || item.hammer > 0) {
				return false;
			}
			if (item.shoot > ProjectileID.None && item.shoot < ProjectileID.Sets.IsAWhip.Length && ProjectileID.Sets.IsAWhip[item.shoot]) {
				return false;
			}
			return item.CountsAsClass(DamageClass.Melee);
		}

		/// <summary>The worn armor's melee-only bonuses beat every other class's (see <see cref="MeleeFocusPlayer"/>).</summary>
		public static bool WearsMeleeArmor(Player player) {
			if (scores == null || player?.armor == null || player.armor.Length < 3) {
				return false;
			}
			float melee = 0f, best = 0f;
			for (int c = 0; c < Classes; c++) {
				float sum = 0f;
				for (int slot = 0; slot < 3; slot++) {
					sum += Score(player.armor[slot], c);
				}
				if (c == 0) {
					melee = sum;
				}
				else if (sum > best) {
					best = sum;
				}
			}
			return melee > 0.001f && melee > best;
		}

		private static float Score(Item item, int c) {
			if (item == null || item.IsAir || item.type <= ItemID.None || item.type >= measured.Length) {
				return 0f;
			}
			if (item.headSlot < 0 && item.bodySlot < 0 && item.legSlot < 0) {
				return 0f;
			}
			if (measured[item.type] == 0) {
				Measure(item.type);
			}
			return scores[item.type * Classes + c];
		}

		/// <summary>One armor piece on the scratch player: its class-only damage, crit and attack speed (plus minions for
		/// summon and mana for magic, so a piece is judged by its main class), as fractions.</summary>
		private static void Measure(int type) {
			measured[type] = 1;
			try {
				scratch ??= new Player { isDisplayDollOrInanimate = true };
				scratch.whoAmI = Main.maxPlayers;                // never the local player (0..254 on a client)
				scratch.isDisplayDollOrInanimate = true;
				scratch.ResetEffects();
				Span<float> before = stackalloc float[Classes];
				Read(scratch, before);
				Item piece = new(type);
				scratch.GrantArmorBenefits(piece);
				Span<float> after = stackalloc float[Classes];
				Read(scratch, after);
				for (int c = 0; c < Classes; c++) {
					float delta = after[c] - before[c];
					scores[type * Classes + c] = float.IsFinite(delta) ? Math.Max(0f, delta) : 0f;
				}
			}
			catch (Exception e) {
				SafeLog.Warn("MeleeGear.Measure", "Couldn't measure armor piece {0}; it counts as no class. {1}", type, e.Message);
				for (int c = 0; c < Classes; c++) {
					scores[type * Classes + c] = 0f;
				}
			}
		}

		private static void Read(Player p, Span<float> into) {
			into[0] = ClassOnly(p, DamageClass.Melee);
			into[1] = ClassOnly(p, DamageClass.Ranged);
			into[2] = ClassOnly(p, DamageClass.Magic) + p.statManaMax2 / 400f;
			into[3] = ClassOnly(p, DamageClass.Summon) + p.maxMinions * 0.1f + p.maxTurrets * 0.05f;
			into[4] = mechanist != null ? ClassOnly(p, mechanist) : 0f;
		}

		private static float ClassOnly(Player p, DamageClass c) {
			StatModifier damage = p.GetDamage(c);
			return (damage.Additive - 1f) + (damage.Multiplicative - 1f) + p.GetCritChance(c) / 100f + (p.GetAttackSpeed(c) - 1f);
		}
	}

	/// <summary>A player's melee verdict: client -> server (only for the sender's own player), server -> the other clients.
	/// A byte and a flag; the player index is validated.</summary>
	public sealed class MeleeFocusPacket : CogpunkPacket
	{
		public void Send(int player, bool focus, int toClient = -1, int ignoreClient = -1) {
			if (Main.netMode == NetmodeID.SinglePlayer) {
				return;
			}
			ModPacket packet = Begin();
			packet.Write((byte)player);
			packet.Write(focus);
			packet.Send(toClient, ignoreClient);
		}

		public override void Receive(BinaryReader reader, int sender) {
			int player = reader.ReadByte();
			bool focus = reader.ReadBoolean();
			if (player < 0 || player >= Main.maxPlayers) {
				return;
			}
			if (Main.netMode == NetmodeID.Server && player != sender) {
				return;                                          // a client speaks only for its own player
			}
			Player p = Main.player[player];
			if (p == null || (Main.netMode == NetmodeID.Server && !p.active)) {
				return;
			}
			p.GetModPlayer<MeleeFocusPlayer>().MeleeFocus = focus;
			if (Main.netMode == NetmodeID.Server) {
				Send(player, focus, -1, sender);                 // tell everyone else
			}
		}
	}

	/// <summary>Shortcuts for boss AI.</summary>
	public static class MeleeFocus
	{
		/// <summary>True while <paramref name="player"/> holds a melee weapon or wears melee armor (any side; the owner's
		/// verdict, synced).</summary>
		public static bool Of(Player player) {
			return player != null && player.active && !player.dead && player.GetModPlayer<MeleeFocusPlayer>().MeleeFocus;
		}
	}
}
