using System;
using System.Collections.Generic;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Manuals
{
	/// <summary>
	/// A crafting manual (user, 2026-11-17: "a consumable item that will serve a greater purpose in the future for a new crafting
	/// unlocking mechanic we will add"): each Cogpunk boss leaves one on its first defeat in a world, one for every player who
	/// fought it, like the treasure bags (<see cref="ManualDrop"/>): the Scrap Manual (Trash-Tr0m), the Sticky Pages (Tar
	/// Tyrant), the Sheriff's Law Book (the Cursed Conductor) and the Jade-shaper Manual (Jadey).
	/// <para>Reading it (a use, held up like a Life Crystal: ExampleMod 1.4.4's <c>ExampleLifeFruit</c>) uses it up and writes
	/// its knowledge into the reader's <see cref="ManualPlayer"/>, saved with the character by the manual's class name, so the
	/// crafting mechanic that comes later can ask <see cref="ManualPlayer.Knows"/>; a second copy can't be read (it can be
	/// sold). Until that mechanic exists the reading only records the knowledge.</para>
	/// <para>So nobody misses it on the ground (user: "floaty and a glow"): it floats where it fell (vanilla's
	/// <c>ItemID.Sets.ItemNoGravity</c>, as souls do), bobbing <see cref="BobPixels"/> px over <see cref="BobTicks"/> ticks in
	/// whole art pixels (D4 rule 17), at full brightness, inside a pulsing ring of its own colour (its <c>_Aura</c> sprite drawn
	/// added, alpha-0 colour in vanilla's premultiplied batch: D4 rule 9), lighting its spot and shedding sparks of its colour
	/// (the Combinator Blueprint's treatment, <see cref="Combinator.Items.CombinatorBlueprint"/>).</para>
	/// <para>D0/D1: the aura is cached once on clients (<see cref="ModContent.HasAsset"/> first); the draw is one or two
	/// sprites, no allocation; sparks on clients only, one in <see cref="SparkOneIn"/> ticks. D2: drawing and light are
	/// client-side; the reading runs on the reader's own client (<see cref="UseItem"/>), the knowledge is that player's.</para>
	/// </summary>
	public abstract class CraftingManual : CogpunkItem
	{
		public const int BobTicks = 120;
		public const int BobPixels = 2;                 // screen px either way: one art px (2x art) up and down
		public const int PulseTicks = 90;
		public const int SparkOneIn = 7;
		private static LocalizedText learnedText, alreadyText;

		private Asset<Texture2D> aura;

		/// <summary>This manual's world flag (<see cref="WorldFlagSystem"/>, saved by name): set when it has dropped in this world.</summary>
		public int DroppedFlag { get; private set; } = -1;

		/// <summary>The light it gives off on the ground (r, g, b in 0..1).</summary>
		protected abstract Vector3 GlowLight { get; }

		/// <summary>The dust of the sparks it sheds on the ground.</summary>
		protected abstract int SparkDust { get; }

		protected virtual int Rarity => ItemRarityID.Orange;

		protected virtual int SellGold => 1;

		/// <summary>The name its knowledge is saved under: the class name (a rename needs <c>[LegacyName]</c> and a migration).</summary>
		public string Knowledge => Name;

		public override void Load() {
			DroppedFlag = WorldFlagSystem.Register("Dropped" + Name);
		}

		public override void SetStaticDefaults() {
			Cogpunk.Core.Systems.CogpunkSets.NeverStolen[Type] = true;        // a once-only drop: no thief takes it (2026-11-26)
			Item.ResearchUnlockCount = 1;
			ItemID.Sets.ItemNoGravity[Type] = true;
			learnedText = Mod.GetLocalization("Manuals.Learned");
			alreadyText = Mod.GetLocalization("Manuals.AlreadyRead");
			if (!Main.dedServ && ModContent.HasAsset(Texture + "_Aura")) {
				aura = ModContent.Request<Texture2D>(Texture + "_Aura");
			}
		}

		public override void Unload() {
			learnedText = alreadyText = null;
			aura = null;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 32;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.useTime = 30;
			Item.useAnimation = 30;
			Item.UseSound = SoundID.Item4;
			Item.consumable = true;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(gold: SellGold);
			Item.rare = Rarity;
		}

		public override bool CanUseItem(Player player) => !player.GetModPlayer<ManualPlayer>().Knows(Knowledge);

		public override bool? UseItem(Player player) {
			ManualPlayer reader = player.GetModPlayer<ManualPlayer>();
			if (!reader.Learn(Knowledge)) {
				return null;                                   // never used up twice
			}
			if (player.whoAmI == Main.myPlayer && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = 0.3f, Volume = 0.6f }, player.Center);
				if (learnedText != null) {
					CombatText.NewText(player.getRect(), new Color(238, 241, 243), learnedText.Format(Item.Name));
				}
				// research (user, 2026-11-18: "when players use the manual consumables that some bosses drop it should reveal players
				// new secret nodes to unlock ... with a chat message "Knowledge expanded""): the nodes that ask for this manual
				// (ResearchNode.Reveal) now show in the reader's research tree
				Main.NewText(Terraria.Localization.Language.GetTextValue("Mods.Cogpunk.Research.KnowledgeExpanded"), new Color(223, 185, 78));
				Research.ResearchPlayer research = player.GetModPlayer<Research.ResearchPlayer>();
				research.QuietReveals();                         // this line already says it: the reveal check stays quiet
				research.MarkDirty();
			}
			return true;
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			if (alreadyText != null && Main.LocalPlayer.GetModPlayer<ManualPlayer>().Knows(Knowledge)) {
				tooltips.Add(new TooltipLine(Mod, "AlreadyRead", alreadyText.Value) { OverrideColor = new Color(190, 120, 120) });
			}
		}

		public override Color? GetAlpha(Color lightColor) => Color.White;     // full brightness, like a soul

		public override void Update(ref float gravity, ref float maxFallSpeed) {
			Vector3 light = GlowLight;
			Lighting.AddLight(Item.Center, light.X, light.Y, light.Z);
			if (Main.dedServ || !Main.rand.NextBool(SparkOneIn) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 at = Item.Center + new Vector2(Main.rand.NextFloat(-12f, 12f), Main.rand.NextFloat(-8f, 10f));
			if (SafeSpawn.TryNewDust(at, 0, 0, SparkDust, out Dust d)) {
				d.velocity = new Vector2(0f, -Main.rand.NextFloat(0.4f, 1.1f));
				d.noGravity = true;
				d.scale = Main.rand.NextFloat(0.7f, 1.05f);
			}
		}

		/// <summary>The ring of light, then the manual itself a whole art pixel up or down (so it floats), at full brightness.</summary>
		public override bool PreDrawInWorld(SpriteBatch spriteBatch, Color lightColor, Color alphaColor, ref float rotation, ref float scale, int whoAmI) {
			uint tick = Main.GameUpdateCount + (uint)(whoAmI * 37);
			float pulse = 0.7f + 0.3f * MathF.Sin(tick * MathHelper.TwoPi / PulseTicks);
			int bob = (int)MathF.Round(MathF.Sin(tick * MathHelper.TwoPi / BobTicks) * (BobPixels / 2f)) * 2;
			Vector2 centre = Item.Center - Main.screenPosition;
			centre = new Vector2(MathF.Round(centre.X), MathF.Round(centre.Y) + bob);
			if (aura?.IsLoaded == true) {
				Texture2D a = aura.Value;
				spriteBatch.Draw(a, centre, null, new Color(255, 255, 255, 0) * (0.8f * pulse), 0f, new Vector2(a.Width / 2f, a.Height / 2f), 1f,
					SpriteEffects.None, 0f);
			}
			Main.instance.LoadItem(Type);
			Texture2D t = TextureAssets.Item[Type].Value;
			spriteBatch.Draw(t, centre, null, Color.White, 0f, new Vector2(t.Width / 2f, t.Height / 2f), 1f, SpriteEffects.None, 0f);
			return false;
		}
	}
}
