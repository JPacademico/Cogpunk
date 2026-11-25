using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Coghaven.NPCs.CogscorpionRigData;

namespace Cogpunk.Content.Coghaven.NPCs
{
	/// <summary>
	/// Cogscorpion (Escorpião de Engrenagens), a Coghaven enemy (user-set 2026-11-12: "add a new enemy to coghaven being the
	/// cogscorpion"): a palace guardian built like a scorpion, bronze plates edged in red lacquer, a jade head plate and a jade
	/// sting (art/coghaven/make_cogscorpion_art.py).
	/// <para>It skitters at its target (<see cref="WalkSpeed"/>, root-motion frames, D4 rule 14) and hurts by touch alone
	/// (user, 2026-11-24: "the cogscorpions should only deal contact damage so remove the tail attack"; its jade-cursing tail
	/// strike of 2026-11-12 is gone, with its sting). Its sheet keeps the strike's frames, unused.</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; Coghaven is a T4 area): the Demon's numbers in the middle of the
	/// island's two other kinds (terraria.wiki.gg: 120 life, 8 defense, 32 contact in Classic = 240 / 8 / 64 in Expert):
	/// <see cref="Life"/> life, <see cref="Defense"/> defense (bronze), <see cref="ContactDamage"/> contact. Drops 1-2 Jade 1 time
	/// in <see cref="JadeOdds"/> (the Golem's rate).</para>
	/// <para>D2: vanilla's walker sync (ai[0]/ai[1], the template's state and timer). Effects client-side.</para>
	/// </summary>
	public class Cogscorpion : GridWalkerNPC
	{
		public const int Life = 380, ContactDamage = 56, Defense = 16;
		public const float WalkSpeed = 1.6f, WalkAccel = 0.08f, JumpSpeed = 6.5f;
		public const int JadeOdds = 4, JadeMin = 1, JadeMax = 2;
		public const float SpawnWeight = 1f;
		public const float Value = 900f;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Cogscorpion_GoreTail", "Cogscorpion_GoreClaw", "Cogscorpion_GoreBody" };

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement;

		protected override float GlowStrength => 0.8f;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			far = near = glow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;    // bronze and jade
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = 60;                                  // the carapace and head (D4: matched hitbox; the tail is the sting's)
			NPC.height = 30;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0.5f;
			NPC.HitSound = SoundID.NPCHit4;                  // metal
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Value;
			NPC.aiStyle = -1;
			SpawnModBiomes = new[] { ModContent.GetInstance<CoghavenBiome>().Type };
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), JadeOdds, JadeMin, JadeMax));
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			return CoghavenSpawnRules.SpawnWeight(spawnInfo, SpawnWeight);
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			Run(target != null ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
			FaceMotion(dir);
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Clients: a puff of steam from its vents now and then.</summary>
		private void Effects() {
			if (Main.rand.NextBool(90) && CogpunkClientConfig.RollEffect()) {
				Vector2 vent = NPC.Bottom + new Vector2(10f * -NPC.direction, -28f);
				if (SafeSpawn.TryNewDust(vent, 2, 2, DustID.Smoke, out Dust s, 0f, -1f, 120, new Color(238, 241, 243), 0.9f)) {
					s.noGravity = true;
				}
			}
		}

		protected override int PickFrame() {
			if (!Grounded) {
				return R.Walk + 1;
			}
			if (Math.Abs(NPC.velocity.X) > 0.1f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= R.WalkStep * R.WalkFrames) {
					NPC.frameCounter -= R.WalkStep * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / R.WalkStep) % R.WalkFrames;
			}
			return R.Walk;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 16;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.GemEmerald : DustID.Copper, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center, NPC.velocity * 0.4f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
				}
			}
		}
	}
}
