using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Items
{
	/// <summary>
	/// Combinator Blueprint (Planta do Combinador): rolled-up blueprint paper with a brass seal, the Wall of Flesh's drop on the
	/// first kill in a world only (user, 2026-11-12: "only on the first kill, make it float and with an aura ray when dropped so
	/// the players don't miss it"; <see cref="CombinatorSystem"/>'s <see cref="BlueprintDrop"/>). A material for
	/// <see cref="TheCombinator"/>.
	/// <para>On the ground it floats where it fell (vanilla's <c>ItemID.Sets.ItemNoGravity</c>, as souls do: the Wall dies
	/// over the Underworld's lava lakes), glows at full brightness and lights its spot, and stands in a column of light: a
	/// pixel-art beam <see cref="BeamSegments"/> segments tall, brightest at the bottom, with a ring of light round it, both
	/// pulsing (drawn added on, with alpha-0 colours in vanilla's premultiplied batch, faded in code: D4 rule 9), and sparks
	/// rising up it. Not White rarity, so vanilla's lava never burns it (decompiled <c>Item.CheckLavaDeath</c>: only rarity 0).</para>
	/// <para>D1/D2: the beam and the sparks are client drawing; the light is <c>Lighting.AddLight</c> (nothing on a server).
	/// Textures cached once on clients.</para>
	/// </summary>
	public class CombinatorBlueprint : CogpunkItem
	{
		public const int BeamSegments = 12;          // 12 x 32 px: a column 24 tiles tall
		public const int PulseTicks = 90;
		private static Asset<Texture2D> beam, aura;

		public override void SetStaticDefaults() {
			Cogpunk.Core.Systems.CogpunkSets.NeverStolen[Type] = true;        // a once-only drop: no thief takes it (2026-11-26)
			Item.ResearchUnlockCount = 1;
			ItemID.Sets.ItemNoGravity[Type] = true;
			ItemID.Sets.ItemIconPulse[Type] = true;
			if (!Main.dedServ) {
				beam = Optional(Texture + "_Beam");
				aura = Optional(Texture + "_Aura");
			}
		}

		private static Asset<Texture2D> Optional(string path) => ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;

		public override void Unload() {
			beam = aura = null;
		}

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 30;
			Item.maxStack = 1;
			Item.value = Item.sellPrice(gold: 5);
			Item.rare = ItemRarityID.LightRed;
		}

		public override Color? GetAlpha(Color lightColor) => Color.White;     // full brightness, like a soul

		public override void Update(ref float gravity, ref float maxFallSpeed) {
			Lighting.AddLight(Item.Center, 0.95f, 0.75f, 0.32f);
			if (Main.dedServ || !Main.rand.NextBool(6) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 at = Item.Center + new Vector2(Main.rand.NextFloat(-5f, 5f), -Main.rand.NextFloat(0f, 120f));
			if (SafeSpawn.TryNewDust(at, 0, 0, DustID.GoldFlame, out Dust d)) {
				d.velocity = new Vector2(0f, -Main.rand.NextFloat(0.6f, 1.6f));
				d.noGravity = true;
				d.scale = Main.rand.NextFloat(0.7f, 1.1f);
			}
		}

		/// <summary>The beam and the ring, behind the item; then vanilla draws the item itself.</summary>
		public override bool PreDrawInWorld(SpriteBatch spriteBatch, Color lightColor, Color alphaColor, ref float rotation, ref float scale, int whoAmI) {
			float pulse = 0.75f + 0.25f * MathF.Sin(Main.GameUpdateCount * MathHelper.TwoPi / PulseTicks);
			Vector2 centre = Item.Center - Main.screenPosition;
			centre = new Vector2(MathF.Round(centre.X), MathF.Round(centre.Y));
			Color light = new Color(255, 255, 255, 0);
			if (beam?.IsLoaded == true) {
				Texture2D t = beam.Value;
				for (int k = 0; k < BeamSegments; k++) {
					float fade = 1f - k / (float)BeamSegments;
					Vector2 at = centre - new Vector2(t.Width / 2f, t.Height * (k + 1));
					spriteBatch.Draw(t, at, null, light * (0.55f * fade * pulse), 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
				}
			}
			if (aura?.IsLoaded == true) {
				Texture2D a = aura.Value;
				spriteBatch.Draw(a, centre, null, light * (0.7f * pulse), 0f, new Vector2(a.Width / 2f, a.Height / 2f), 1f, SpriteEffects.None, 0f);
			}
			return true;
		}
	}
}
