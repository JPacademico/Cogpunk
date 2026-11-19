using System;
using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// The <see cref="IncenseMace"/>'s censer on its chain: vanilla's flail AI (<c>ProjAIStyleID.Flail</c>, ExampleMod 1.4.4's
	/// <c>ExampleFlailProjectile</c>) under its own type, so none of vanilla's per-flail dust or sounds apply, with the Sunfury's
	/// throw and retract speeds (<see cref="FlailStats"/>, decompiled 1.4.4 <c>Projectile.AI_015_Flails</c>, case 35). It
	/// trails incense smoke (a puff every <see cref="SmokeOneIn"/> ticks, fewer while it spins).
	/// <para>Drawn by hand: the gilt chain from the wielder's hand to the censer, a link every <see cref="LinkLength"/> px
	/// (at most <see cref="MaxLinks"/>, D0), turned along the chain as vanilla's flail chains are; the censer always upright
	/// (it hangs: it is never turned), on whole pixels.</para>
	/// <para>D2: vanilla's flail sync (the owner's input drives the AI's state in <c>ai[0]</c>); visuals on clients only.</para>
	/// </summary>
	public class IncenseMaceHead : CogpunkProjectile
	{
		public const int MaxLinks = 48;
		public const float LinkLength = 8f;
		public const int SmokeOneIn = 4;

		private static Asset<Texture2D> chain;

		public override void SetStaticDefaults() {
			ProjectileID.Sets.HeldProjDoesNotUsePlayerGfxOffY[Type] = true;
			if (!Main.dedServ) {
				const string path = "Cogpunk/Content/Bosses/Jadey/Weapons/IncenseMaceChain";
				chain = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
			}
		}

		public override void Unload() {
			chain = null;
		}

		public override void SetDefaults() {
			Projectile.netImportant = true;                      // synced to players who join while it is out
			Projectile.width = 24;
			Projectile.height = 24;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = 10;
			Projectile.aiStyle = ProjAIStyleID.Flail;
		}

		/// <summary>The Sunfury's numbers (the strongest pre-Hardmode flail; decompiled <c>AI_015_Flails</c>, case 35).</summary>
		public override void FlailStats(ref int launchTimeLimit, ref float launchSpeed, ref float maxLaunchLength, ref float retractAcceleration,
			ref float maxRetractSpeed, ref float forcedRetractAcceleration, ref float maxForcedRetractSpeed, ref int ricochetTimeLimit,
			ref float spinVisualDistance) {
			launchTimeLimit = 15;
			launchSpeed = 17f;
			maxRetractSpeed = 14f;
			maxForcedRetractSpeed = 18f;
			ricochetTimeLimit = launchTimeLimit + 5;
		}

		public override void AI() {
			if (Main.dedServ || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			bool spinning = Projectile.ai[0] == 0f;
			if (Main.rand.NextBool(spinning ? SmokeOneIn * 2 : SmokeOneIn)
				&& SafeSpawn.TryNewDust(Projectile.Center + new Vector2(-4f, -10f), 8, 6, DustID.Smoke, out Dust d, 0f, -0.6f, 120,
					new Color(214, 206, 236))) {
				d.noGravity = true;
				d.scale = 0.75f;
				d.velocity *= 0.4f;
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				return false;
			}
			Vector2 hand = Main.GetPlayerArmPosition(Projectile);
			Vector2 head = Projectile.Center;
			if (chain?.IsLoaded == true) {
				Texture2D link = chain.Value;
				Vector2 along = head - hand;
				float length = along.Length();
				if (float.IsFinite(length) && length > 1f) {
					Vector2 step = along / length * LinkLength;
					float rotation = along.ToRotation() + MathHelper.PiOver2;   // the link art is vertical
					Vector2 origin = link.Size() * 0.5f;
					int links = Math.Min(MaxLinks, (int)(length / LinkLength));
					Vector2 at = hand + step * 0.5f;
					for (int i = 0; i < links; i++, at += step) {
						Color c = Lighting.GetColor((int)(at.X / 16f), (int)(at.Y / 16f));
						Main.EntitySpriteDraw(link, at - Main.screenPosition, null, c, rotation, origin, 1f, SpriteEffects.None);
					}
				}
			}
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			Vector2 pos = head - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Main.EntitySpriteDraw(tex, new Vector2(MathF.Round(pos.X), MathF.Round(pos.Y)), null, Projectile.GetAlpha(lightColor), 0f,
				new Vector2(MathF.Round(tex.Width * 0.5f), MathF.Round(tex.Height * 0.5f)), 1f,
				Projectile.spriteDirection < 0 ? SpriteEffects.FlipHorizontally : SpriteEffects.None);
			return false;
		}
	}
}
