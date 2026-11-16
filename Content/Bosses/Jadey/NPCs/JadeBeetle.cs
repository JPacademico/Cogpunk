using Cogpunk.Content.Coghaven;
using Cogpunk.Content.Gems;
using Cogpunk.Content.Jungle.NPCs;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.NPCs
{
	/// <summary>
	/// Jade Beetle (Besouro de Jade), one of Jadey's coin minions (user, 2026-11-16: "jade beetle (the jade version of the rhino
	/// beetle we already have, weaker because the beetle is from hardmode)"): the <see cref="RhinoBeetle"/>'s body, AI and
	/// frames (its brace, charge, toss, flight), carved in jade over bronze with a gilt vein
	/// (art/coghaven/make_jade_beetle_art.py recolours the Rhino Beetle's sheets), and pre-Hardmode numbers: Coghaven's
	/// tier, T4. Its ram and touch lay a stack of the jade curse (my call, as every jade bite of hers). Only ever made by her
	/// coins (no natural spawn); no loot (<see cref="JadeyMinion"/>).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv): against Coghaven's own Cogscorpion (380 / 16 / 56) and the
	/// Antlion Charger (decompiled 1.4.4 NPC 508: 110 / 16 / 38 Classic = 220 / 16 / 76 Expert, the pre-Hardmode charger):
	/// <see cref="JadeLife"/> life, <see cref="JadeDefense"/> defense, <see cref="JadeContact"/> contact (x1.6 charging), and a
	/// softer ram (x<see cref="JadeRam"/> knockback, a lower toss) than the Hardmode beetle's x2; halved again as her minion.</para>
	/// </summary>
	public class JadeBeetle : RhinoBeetle
	{
		public const int JadeLife = 340, JadeContact = 60, JadeDefense = 18;
		public const float JadeRam = 1.5f, JadeTouch = 1.2f, JadeToss = 7f, JadeResist = 0.4f;
		private static readonly string[] JadeGores = { "JadeBeetle_GoreHorn", "JadeBeetle_GoreShell", "JadeBeetle_GoreLeg" };

		private static Asset<Texture2D> jadeFar, jadeNear, jadeGlow;

		protected override int ExpertLife => JadeLife;
		protected override int ExpertContact => JadeContact;
		protected override int ExpertDefense => JadeDefense;
		protected override float Resist => JadeResist;
		protected override float RamPush => JadeRam;
		protected override float TouchPush => JadeTouch;
		protected override float Toss => JadeToss;
		protected override int CoinValue => 0;
		protected override string[] Gores => JadeGores;
		protected override int BloodDust => DustID.GemEmerald;
		protected override Asset<Texture2D> FarSheet => jadeFar;
		protected override Asset<Texture2D> NearSheet => jadeNear;
		protected override Asset<Texture2D> GlowSheet => jadeGlow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement;

		protected override void LoadSheets() {
			jadeFar = DepthLayers.RequestOptional(Texture + "_Far");
			jadeNear = DepthLayers.RequestOptional(Texture + "_Near");
			jadeGlow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			jadeFar = jadeNear = jadeGlow = null;
		}

		/// <summary>Only Jadey's coins make it.</summary>
		public override float SpawnChance(NPCSpawnInfo spawnInfo) => 0f;

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		protected override void OnBeetleHit(Player target) {
			JadeCursePlayer.Hit(target);
		}
	}
}
