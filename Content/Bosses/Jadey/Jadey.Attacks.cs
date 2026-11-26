using System;
using Cogpunk.Content.Bosses.Jadey.Projectiles;
using Cogpunk.Content.Coghaven.Projectiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.Jadey.JadeyRigData;

namespace Cogpunk.Content.Bosses.Jadey
{
	// Jadey's attacks: the coin on its own clock, and one of the four every 2 s (all server-decided; every side counts the
	// clocks and plays the frames from the synced state).
	public partial class Jadey
	{
		// --- the points her art gives (game px from the origin, facing left; mirrored when she faces right) ------------------

		/// <summary>The origin in the world: the middle under her cushion, with the float's whole-pixel bob.</summary>
		public Vector2 Origin => NPC.Bottom - new Vector2(0f, Bob);

		/// <summary>The float's bob: 0 or 2 px (D4 rule 17: whole pixels), drawing and spawn points alike.</summary>
		public float Bob => CurrentPhase == Phase.Dying ? 0f : (Main.GameUpdateCount / 20 + (uint)NPC.whoAmI) % 2 * 2f;

		private Vector2 RigPoint(int x, int y) => Origin + new Vector2(NPC.spriteDirection == 1 ? -x : x, y);

		/// <summary>Her near paw now (the rope dart's cord leaves it).</summary>
		public Vector2 NearPawWorld {
			get {
				int f = Math.Clamp(BodyFrame(), 0, R.NearX.Length - 1);
				return RigPoint(R.NearX[f], R.NearY[f]);
			}
		}

		/// <summary>Her far paw now (coins leave it): the flick's frame while she flicks, else the body frame's own.</summary>
		public Vector2 FarPawWorld {
			get {
				int f = Math.Clamp(FarFrame(), 0, R.FarX.Length - 1);
				return RigPoint(R.FarX[f], R.FarY[f]);
			}
		}

		/// <summary>Her brow gem (her lasers leave it).</summary>
		public Vector2 GemWorld => RigPoint(R.GemX, R.GemY);

		// --- the cadence ----------------------------------------------------------------------------------------------------

		/// <summary>Server: one of her attacks (never the last one again when another is possible); the channel only with three of
		/// her minions up and its cooldown spent. Retargets first (the shared rule picks).</summary>
		private void StartAttack() {
			if (!EnsureTarget()) {
				return;
			}
			bool channel = healCooldown <= 0 && JadeyMinion.Count(NPC.whoAmI) >= MinMinionsToChannel;
			Span<byte> options = stackalloc byte[4];
			int n = 0;
			options[n++] = (byte)Phase.Whip;
			options[n++] = (byte)Phase.Zone;
			options[n++] = (byte)Phase.Laser;
			if (channel) {
				options[n++] = (byte)Phase.Channel;
			}
			int count = n;
			for (int k = 0; k < count; k++) {
				if (options[k] == lastAttack && count > 1) {
					options[k] = options[count - 1];                // drop the last attack from the draw
					count--;
					break;
				}
			}
			byte pick = options[Main.rand.Next(Math.Max(1, count))];
			lastAttack = pick;
			attackClock = 0;
			aim = Vector2.Zero;
			ChangeState(pick);
			NPC.netUpdate = true;
		}

		// --- the statue (user-set 2026-11-17), every 20% of her life -----------------------------------------------------------

		/// <summary>Server: has another <see cref="StatueStep"/> of her life gone since her last statue?</summary>
		private bool StatueDue() {
			if (statuesDone >= StatueCount || NPC.lifeMax <= 0) {
				return false;
			}
			return NPC.life <= NPC.lifeMax * (1f - StatueStep * (statuesDone + 1));
		}

		private void StartStatue() {
			statuesDone++;
			flickTick = -1;
			aim = Vector2.Zero;
			ChangeState((int)Phase.Statue);
			NPC.netUpdate = true;
		}

		/// <summary>Three coins, a flick each (every side flicks from the synced timer; the server throws), each rolling 1-2 minions;
		/// then she turns to jade for <see cref="StatueTicks"/> ticks, or until her minions are all dead; any still alive then she
		/// drains (<see cref="DoChannel"/>, which heals her).</summary>
		private void DoStatue() {
			int t = (int)Timer;
			for (int k = 0; k < StatueCoins; k++) {
				int at = k * StatueCoinGap;
				if (t == at) {
					flickTick = 0;
				}
				if (IsAuthority && t == at + FlickTicks / 2) {
					ThrowStatueCoin(k);
				}
			}
			if (!IsAuthority || t < PetrifyAt + StatueMinionGrace) {
				return;
			}
			int left = JadeyMinion.Count(NPC.whoAmI);
			if (left > 0 && t < PetrifyAt + StatueTicks) {
				return;
			}
			attackClock = 0;
			lastAttack = (byte)Phase.Channel;
			ChangeState(left > 0 ? (int)Phase.Channel : (int)Phase.Idle);
			NPC.netUpdate = true;
		}

		/// <summary>Server: a statue coin: to her left, near her target, to her right; it carries how many minions it hatches (1-2)
		/// and which (<see cref="JadeCoin.StatueCode"/>).</summary>
		private void ThrowStatueCoin(int k) {
			float toward = CurrentTarget is Player p && p.Center.X < NPC.Center.X ? -1f : 1f;
			float dir = k == 0 ? -1f : k == StatueCoins - 1 ? 1f : 0.35f * toward;
			Vector2 v = new(dir * Main.rand.NextFloat(2.6f, 4.2f), -Main.rand.NextFloat(6f, 7.2f));
			int count = Main.rand.Next(1, 3);
			int first = JadeCoin.RollKind(), second = JadeCoin.RollKind();
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), FarPawWorld, v, ModContent.ProjectileType<JadeCoin>(), 0, 0f, out _,
				ai0: first, ai1: NPC.whoAmI, ai2: JadeCoin.StatueCode(count, first, second));
		}

		private void EndAttack() {
			if (IsAuthority) {
				aim = Vector2.Zero;
				ChangeState((int)Phase.Idle);
			}
		}

		// --- the coin, every 4 s ---------------------------------------------------------------------------------------------

		/// <summary>Every side counts; the server flicks a coin every <see cref="CoinInterval"/> ticks (rolling what it hatches),
		/// unless she already has <see cref="MaxMinions"/> minions (then it waits). The flick is drawn from the synced
		/// <c>flickTick</c>; the coin leaves her far paw at the flick's top.</summary>
		private void UpdateCoin() {
			coinClock++;
			if (!IsAuthority) {
				return;
			}
			if (coinClock == CoinInterval) {
				if (JadeyMinion.Count(NPC.whoAmI) >= MaxMinions) {
					coinClock = 0;                                 // at her cap: this coin is skipped (my call)
					return;
				}
				flickTick = 0;                                     // the flick starts; the coin leaves at its top
				nextKind = (byte)JadeCoin.RollKind();
				NPC.netUpdate = true;
			}
			if (coinClock == CoinInterval + FlickTicks / 2) {
				if (CurrentTarget is Player target) {
					float dir = target.Center.X >= NPC.Center.X ? 1f : -1f;
					Vector2 v = new(dir * Main.rand.NextFloat(2.2f, 4.2f), -Main.rand.NextFloat(5.5f, 7f));
					SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), FarPawWorld, v, ModContent.ProjectileType<JadeCoin>(), 0, 0f, out _,
						ai0: nextKind, ai1: NPC.whoAmI);
				}
				coinClock = 0;
				NPC.netUpdate = true;
			}
		}

		// --- 1: the rope dart ------------------------------------------------------------------------------------------------

		/// <summary>The spin (the telegraph, <see cref="SpinTicks"/>), then the throw at where the target will be; the cord is held
		/// while the dart flies and comes home.</summary>
		private void DoWhip() {
			int t = (int)Timer;
			if (IsAuthority && t >= 1 && t < SpinTicks && CurrentTarget is Player p) {
				aim = Lead(p, NearPawWorld);                      // the aim line follows the lead while she spins
				if (t % 6 == 0) {
					NPC.netUpdate = true;
				}
			}
			if (IsAuthority && t == SpinTicks) {
				Player target = CurrentTarget;
				if (target != null) {
					Vector2 from = NearPawWorld;
					aim = Lead(target, from);
					Vector2 dir = (aim - from).SafeNormalize(new Vector2(NPC.spriteDirection, 0f));
					int damage = ExpertStats.HostileProjectile(NPC, DartDamage);
					SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, dir * (JadeyRopeDart.Speed * 0.5f), ModContent.ProjectileType<JadeyRopeDart>(),
						damage, 0f, out _, ai0: NPC.whoAmI);
				}
				NPC.netUpdate = true;
			}
			if (t >= WhipTicks) {
				EndAttack();
			}
		}

		/// <summary>Where a dart from <paramref name="from"/> meets <paramref name="target"/> if it keeps moving as it does
		/// ("predicting player movement"): two passes of distance over speed, the lead capped at <see cref="LeadMax"/>.</summary>
		private static Vector2 Lead(Player target, Vector2 from) {
			Vector2 to = target.Center;
			for (int pass = 0; pass < 2; pass++) {
				float time = Vector2.Distance(from, to) / JadeyRopeDart.Speed;
				Vector2 lead = target.velocity * time;
				if (lead.LengthSquared() > LeadMax * LeadMax) {
					lead = lead.SafeNormalize(Vector2.Zero) * LeadMax;
				}
				to = target.Center + lead;
			}
			return MathSafety.IsFinite(to) ? to : target.Center;
		}

		// --- 2: the petrify zone ---------------------------------------------------------------------------------------------

		/// <summary>The band is laid under the target as her arms rise; it snaps on its own clock; she slams her paws down with it.</summary>
		private void DoZone() {
			int t = (int)Timer;
			if (IsAuthority && t == 1 && CurrentTarget is Player target) {
				int tx = (int)(target.Center.X / 16f);
				int ground = FindGround(tx, (int)(target.Bottom.Y / 16f), out int g) ? g : (int)(target.Bottom.Y / 16f);
				int left = tx - JadePetrifyZone.WidthTiles / 2;
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), new Vector2(left * 16f, ground * 16f), Vector2.Zero,
					ModContent.ProjectileType<JadePetrifyZone>(), 0, 0f, out _, ai0: left, ai1: ground);
				aim = new Vector2(left * 16f + JadePetrifyZone.WidthTiles * 8f, ground * 16f);
				NPC.netUpdate = true;
			}
			if (t >= ZoneTicks) {
				EndAttack();
			}
		}

		/// <summary>The first solid floor at or below (<paramref name="x"/>, <paramref name="y"/>) with air over it, within
		/// <see cref="ZoneGroundScan"/> rows (bounded, bounds-checked): the row of that floor tile.</summary>
		private static bool FindGround(int x, int y, out int ground) {
			ground = 0;
			for (int k = 0; k < ZoneGroundScan; k++) {
				int yy = y + k;
				if (TileSafety.TryGetTile(x, yy, out Tile tile) && tile.HasTile && !tile.IsActuated
					&& (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType])
					&& TileSafety.TryGetTile(x, yy - 1, out Tile above) && !(above.HasTile && Main.tileSolid[above.TileType] && !above.IsActuated)) {
					ground = yy;
					return true;
				}
			}
			return false;
		}

		// --- 3: the channel ---------------------------------------------------------------------------------------------------

		/// <summary>1.2 s with her eyes aglow, then her minions are drawn into her and she heals (none left: nothing).</summary>
		private void DoChannel() {
			int t = (int)Timer;
			if (IsAuthority && t == ChannelTicks) {
				int eaten = 0;
				foreach (NPC npc in Main.ActiveNPCs) {
					if (JadeyMinion.Of(npc, NPC.whoAmI)) {
						JadeyMinion.Consume(npc);
						eaten++;
					}
				}
				if (eaten > 0) {
					int heal = (int)(NPC.lifeMax * HealFraction);
					NPC.life = Math.Min(NPC.lifeMax, NPC.life + heal);
					NPC.HealEffect(heal);
					NPC.netUpdate = true;
				}
				healCooldown = HealCooldown;
				NPC.netUpdate = true;
			}
			if (t >= ChannelTicks + ChannelRecover) {
				EndAttack();
			}
		}

		// --- 4: the lasers ----------------------------------------------------------------------------------------------------

		/// <summary>The tick of laser <paramref name="k"/> (0-based) within the attack.</summary>
		public static int LaserTick(int k) => LaserAim + k * LaserGap;

		/// <summary>She aims from her brow; three lasers 0.3 s apart, each at where the target is then.</summary>
		private void DoLaser() {
			int t = (int)Timer;
			for (int k = 0; k < LaserShots; k++) {
				if (IsAuthority && t == LaserTick(k) && CurrentTarget is Player target) {
					Vector2 from = GemWorld;
					Vector2 dir = (target.Center - from).SafeNormalize(new Vector2(NPC.spriteDirection, 0f));
					float length = JadeRay.RayLength(from, dir, JadeRay.MaxLength);
					int damage = ExpertStats.HostileProjectile(NPC, LaserDamage);
					SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, Vector2.Zero, ModContent.ProjectileType<JadeRay>(), damage, 0f, out _,
						ai0: MathF.Atan2(dir.Y, dir.X), ai1: length, ai2: JadeRay.JadeyLaserFlag);
				}
			}
			if (t >= LaserTicks) {
				EndAttack();
			}
		}

		// --- frames (shared by drawing and the spawn points: a pure function of the synced state) -----------------------------

		/// <summary>The body frame now (the middle and near planes, the glow).</summary>
		public int BodyFrame() {
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Intro:
					return R.Intro + (t < 50 ? 0 : t < 70 ? 1 : t < 100 ? 2 : 3);
				case Phase.Whip:
					if (t < 6) {
						return R.Whip;
					}
					if (t < 12) {
						return R.Whip + 1;
					}
					if (t < SpinTicks) {
						return R.Whip + 2 + (t / 3) % 2;
					}
					return R.Whip + (t < SpinTicks + 16 ? 4 : t < WhipTicks - 10 ? 4 : 5);
				case Phase.Zone:
					if (t < 10) {
						return R.Zone;
					}
					if (t < 20) {
						return R.Zone + 1;
					}
					if (t < JadePetrifyZone.SnapTick) {
						return R.Zone + 2 + (t / 6) % 2;
					}
					return R.Zone + (t < JadePetrifyZone.SnapTick + 10 ? 4 : 5);
				case Phase.Channel:
					if (t < 10) {
						return R.Channel;
					}
					if (t < 20) {
						return R.Channel + 1;
					}
					if (t < ChannelTicks) {
						return R.Channel + 2 + (t / 6) % 2;
					}
					return R.Channel + (t < ChannelTicks + 9 ? 1 : 0);
				case Phase.Laser:
					if (t < 8) {
						return R.Laser;
					}
					if (t >= LaserTick(LaserShots - 1) + 8) {
						return R.Laser + 3;
					}
					for (int k = 0; k < LaserShots; k++) {
						if (t >= LaserTick(k) && t < LaserTick(k) + 6) {
							return R.Laser + 2;                      // the flash of a shot
						}
					}
					return R.Laser + 1;
				case Phase.Leave:
					return R.Intro + (t < 20 ? 3 : 1);
				case Phase.Dying:
					if (t < 100) {
						return R.Death + Math.Min(4, t / 20);         // the jade creeps up her
					}
					return R.Death + (t < 140 ? 5 : t < 170 ? 6 : 7);
				case Phase.Statue:
					if (t < PetrifyAt) {
						return R.Idle + (int)((Main.GameUpdateCount / 9 + (uint)NPC.whoAmI) % R.IdleFrames);   // the coins (far-arm flicks)
					}
					if (t < PetrifyAt + PetrifyTurnTicks) {
						return R.Death + Math.Min(4, (t - PetrifyAt) * 5 / PetrifyTurnTicks);   // the jade creeps up her, fast
					}
					return R.Death + (t >= PetrifyAt + StatueTicks - StatueCrackWarn ? 6 : 5);    // a statue; cracks before she wakes
				default:
					return R.Idle + (int)((Main.GameUpdateCount / 9 + (uint)NPC.whoAmI) % R.IdleFrames);
			}
		}

		/// <summary>The far plane's frame: the coin flick (six frames over <see cref="FlickTicks"/>) where the body frame's far
		/// arm rests, else the body frame's own far arm.</summary>
		public int FarFrame() {
			int body = BodyFrame();
			if (flickTick >= 0 && body >= 0 && body < R.FlickOk.Length && R.FlickOk[body]) {
				return R.Flick + Math.Clamp(flickTick * R.FlickFrames / (FlickTicks + 1), 0, R.FlickFrames - 1);
			}
			return body;
		}
	}
}
