using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// The Scrap Launcher's impact (user-set 2026-10-27: the shots used to just vanish on an enemy): a brass-and-aether
	/// starburst drawn by this dust over <see cref="Frames"/> frames, scrap shards and bolts flung out of it, a steam puff and
	/// a crunch. <see cref="Burst"/> is called from the projectiles' <c>OnKill</c>, which every client runs (the owner kills
	/// the projectile on the hit and vanilla tells the others), so everyone sees it.
	/// <para>Sheet (art/bosses/trashtr0m/make_trashtr0m_loot.py, ScrapImpact.png): two columns of <see cref="Frames"/>
	/// frames, the chunk's <see cref="SmallSize"/> px burst on the left and the ball's <see cref="BigSize"/> px burst on the
	/// right, on a 2 px gap. Drawn centred at whole pixels and full-bright (it is a flash), never rotated or scaled (D4).
	/// D1: client-only, one dust per hit.</para>
	/// </summary>
	public class ScrapImpact : ModDust
	{
		public const int Frames = 5;
		public const int TicksPerFrame = 3;
		public const int SmallSize = 48, BigSize = 80;
		private const int BigColumn = SmallSize + 2;

		public override string Texture => TextureFallback.Resolve(base.Texture);

		public override void OnSpawn(Dust dust) {
			dust.noGravity = true;
			dust.noLight = false;
			dust.velocity = Vector2.Zero;
			dust.frame = new Rectangle(0, 0, SmallSize, SmallSize);
			dust.alpha = 0;
			dust.fadeIn = 0f;
		}

		public override bool Update(Dust dust) {
			bool big = dust.customData is bool b && b;
			int size = big ? BigSize : SmallSize;
			int frame = (int)dust.fadeIn / TicksPerFrame;
			if (frame >= Frames) {
				dust.active = false;
				return false;
			}
			dust.frame = new Rectangle(big ? BigColumn : 0, frame * (size + 2), size, size);
			dust.fadeIn++;
			Lighting.AddLight(dust.position, 0.45f * (1f - frame / (float)Frames), 0.35f * (1f - frame / (float)Frames), 0.15f);
			return false;
		}

		public override Color? GetAlpha(Dust dust, Color lightColor) => Color.White;

		public override bool PreDraw(Dust dust) {
			Texture2D texture = Texture2D.Value;
			Vector2 at = dust.position - Main.screenPosition;
			Vector2 topLeft = new((int)(at.X - dust.frame.Width * 0.5f), (int)(at.Y - dust.frame.Height * 0.5f));
			Main.spriteBatch.Draw(texture, topLeft, dust.frame, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
			return false;
		}

		/// <summary>Clients: the full impact at <paramref name="at"/> for a shot travelling at <paramref name="velocity"/>.</summary>
		public static void Burst(Vector2 at, Vector2 velocity, bool big) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound((big ? SoundID.Item14 : SoundID.Item52) with { Pitch = big ? -0.3f : -0.1f, Volume = big ? 0.8f : 0.6f, MaxInstances = 4 }, at);
			if (big) {
				SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.6f }, at);
			}
			if (SafeSpawn.TryNewDust(at, 0, 0, ModContent.DustType<ScrapImpact>(), out Dust flash)) {
				flash.position = at;                         // NewDust offsets by up to 4 px: put it back on the hit
				flash.customData = big;
			}
			Vector2 back = -velocity.SafeNormalize(Vector2.Zero);
			int shards = big ? 18 : 8;
			for (int i = 0; i < shards; i++) {
				if (i >= 4 && !CogpunkClientConfig.RollEffect()) {
					continue;
				}
				// shards fly back out of the hit and up, bolts (brass) and rust flakes (iron/copper)
				Vector2 v = (back * Main.rand.NextFloat(1f, big ? 5f : 3.5f) + Main.rand.NextVector2Circular(big ? 5f : 3f, big ? 5f : 3f))
					- new Vector2(0f, Main.rand.NextFloat(0.5f, 2.5f));
				int type = i % 3 == 0 ? DustID.Enchanted_Gold : (i % 3 == 1 ? DustID.Iron : DustID.Copper);
				if (SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, type, out Dust d, v.X, v.Y, 0, default, big ? 1.3f : 1f)) {
					d.velocity = v;
					d.noGravity = type == DustID.Enchanted_Gold;
				}
			}
			int puffs = big ? 6 : 2;
			for (int i = 0; i < puffs; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(8f), 16, 16, DustID.Smoke, out Dust s, 0f, -1f, 100, new Color(195, 200, 205), big ? 1.6f : 1.1f)) {
					s.velocity = Main.rand.NextVector2Circular(1.5f, 1.5f) - new Vector2(0f, 0.6f);
					s.noGravity = true;
				}
			}
		}
	}
}
