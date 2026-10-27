using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// The Trapper Chain's bear trap on its chain (see <see cref="TrapperChain"/>). It flies out with its jaws open up to
	/// <see cref="MaxReach"/> from the player and snaps shut on the first enemy it reaches. The bite lands on every enemy
	/// overlapping the trap while the jaws slam shut (user-set 2026-10-27: hits stay allowed for <see cref="BiteTicks"/>
	/// ticks from the first one; vanilla's <c>Projectile.Damage</c> tries every NPC each tick, and the trap still drifts a
	/// little forward into a pack before the reel-in turns it), each enemy at most once; then it is reeled back in. A tile it
	/// hits sends it back too. While it's out it holds the owner's use (<c>Player.SetDummyItemTime</c>, as vanilla's
	/// tethered projectiles do), so the next throw comes as soon as it's back, but never sooner than
	/// <see cref="TrapperChain.MinCycleTicks"/> after the throw. The chain is drawn link by link from the player's hand like
	/// vanilla's flails and harpoons (ExampleMod 1.4.4 flail drawing), at most <see cref="MaxLinks"/> links (D0).
	/// <para>D2: <c>ai[0]</c> = returning, <c>ai[1]</c> = snapped (jaws shut); the owner decides both and syncs on change.
	/// The path is plain velocity on every side; hits are the owner's. D1: no allocation; the chain is a loop of draws.</para>
	/// </summary>
	public class TrapperChainProjectile : CogpunkProjectile
	{
		public const float MaxReach = 18f * 16f;
		public const float ReturnSpeed = 16f;
		public const float ReturnAccel = 0.8f;
		public const int MaxLinks = 64;
		public const int BiteTicks = 3;                    // the jaws bite everything they overlap for this long
		public const int HeadFrames = 2;                  // open, shut
		public const int HeadWidth = 32, HeadHeight = 28, HeadStride = 30;
		private const float LinkLength = 10f;

		private static Asset<Texture2D> link;

		private ref float Returning => ref Projectile.ai[0];
		private ref float Snapped => ref Projectile.ai[1];
		private ref float Age => ref Projectile.localAI[0];   // ticks since the throw (each side counts its own)

		private int biteAge = -1;                         // owner: ticks since the jaws shut (-1: still open)

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = HeadFrames;
			if (!Main.dedServ) {
				const string path = "Cogpunk/Content/Mechanist/Weapons/TrapperChainLink";
				link = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
			}
		}

		public override void Unload() {
			link = null;
		}

		public override void SetDefaults() {
			Projectile.width = 22;
			Projectile.height = 22;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.tileCollide = true;
			Projectile.timeLeft = 180;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			if (!owner.active || owner.dead) {
				Projectile.Kill();
				return;
			}
			Age++;
			if (biteAge >= 0) {
				biteAge++;
			}
			owner.SetDummyItemTime(2);                     // the throw lasts until the trap is back
			Vector2 hand = owner.MountedCenter;
			Vector2 toHand = hand - Projectile.Center;
			float distance = toHand.Length();
			if (Returning == 0f) {
				if (distance > MaxReach && Projectile.owner == Main.myPlayer) {
					StartReturn();
				}
			}
			else {
				Projectile.tileCollide = false;
				Vector2 want = toHand.SafeNormalize(Vector2.Zero) * ReturnSpeed;
				Projectile.velocity = Vector2.Lerp(Projectile.velocity, want, 0.25f) + toHand.SafeNormalize(Vector2.Zero) * ReturnAccel;
				if (distance < 24f) {
					Projectile.Kill();
					return;
				}
			}
			Projectile.timeLeft = Math.Max(Projectile.timeLeft, 2);
			Projectile.frame = Snapped != 0f ? 1 : 0;
			Vector2 heading = Returning == 0f ? Projectile.velocity : -toHand;
			Projectile.rotation = heading.ToRotation();
			Projectile.direction = heading.X >= 0f ? 1 : -1;
			owner.ChangeDir(Projectile.Center.X >= owner.Center.X ? 1 : -1);
			owner.itemRotation = (toHand * -owner.direction).ToRotation();
		}

		private void StartReturn() {
			if (Returning != 0f) {
				return;
			}
			Returning = 1f;
			Projectile.netUpdate = true;
		}

		/// <summary>Open jaws hit; once they bite, everything they overlap for <see cref="BiteTicks"/> ticks (each enemy once:
		/// local immunity with no cooldown).</summary>
		public override bool? CanHitNPC(NPC target) => Snapped == 0f || (biteAge >= 0 && biteAge < BiteTicks) ? null : false;

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (Projectile.owner == Main.myPlayer && Snapped == 0f) {
				Snapped = 1f;
				biteAge = 0;
				StartReturn();
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item37 with { Pitch = -0.5f }, Projectile.Center);   // the jaws snap
				for (int i = 0; i < 6; i++) {
					SafeSpawn.TryNewDust(target.Center - new Vector2(6f), 12, 12, i % 2 == 0 ? DustID.Iron : DustID.Blood, out _);
				}
			}
		}

		/// <summary>Back in the hand (or gone): the next throw may come right away, but no sooner than
		/// <see cref="TrapperChain.MinCycleTicks"/> after this one.</summary>
		public override void OnKill(int timeLeft) {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				return;
			}
			Player owner = Main.player[Projectile.owner];
			if (owner.active && !owner.dead) {
				owner.SetDummyItemTime(Math.Max(2, TrapperChain.MinCycleTicks - (int)Age));
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Projectile.owner == Main.myPlayer) {
				StartReturn();
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Dig with { Pitch = 0.3f, Volume = 0.6f }, Projectile.Center);
				Collision.HitTiles(Projectile.position, oldVelocity, Projectile.width, Projectile.height);
			}
			Projectile.velocity = -oldVelocity * 0.3f;
			return false;
		}

		public override bool PreDraw(ref Color lightColor) {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				return false;
			}
			Player owner = Main.player[Projectile.owner];
			Vector2 hand = owner.MountedCenter;
			Vector2 head = Projectile.Center;
			if (link?.IsLoaded == true) {
				Texture2D chain = link.Value;
				Vector2 along = head - hand;
				float length = along.Length();
				Vector2 step = along.SafeNormalize(Vector2.UnitX) * LinkLength;
				float rotation = along.ToRotation() + MathHelper.PiOver2;   // the link art is vertical
				Vector2 origin = chain.Size() * 0.5f;
				int links = Math.Min(MaxLinks, (int)(length / LinkLength));
				Vector2 at = hand + step * 0.5f;
				for (int i = 0; i < links; i++, at += step) {
					Color c = Lighting.GetColor((int)(at.X / 16f), (int)(at.Y / 16f));
					Main.EntitySpriteDraw(chain, at - Main.screenPosition, null, c, rotation, origin, 1f, SpriteEffects.None);
				}
			}
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * HeadStride, HeadWidth, HeadHeight);
			SpriteEffects effects = Projectile.direction < 0 ? SpriteEffects.FlipVertically : SpriteEffects.None;   // lit side stays up
			Main.EntitySpriteDraw(texture, head - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY), source, Projectile.GetAlpha(lightColor),
				Projectile.rotation, new Vector2(HeadWidth * 0.5f, HeadHeight * 0.5f), 1f, effects);
			return false;
		}
	}
}
