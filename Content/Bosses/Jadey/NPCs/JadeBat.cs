using Cogpunk.Content.Coghaven;
using Cogpunk.Content.Gems;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.NPCs
{
	/// <summary>
	/// Jade Bat (Morcego de Jade), one of Jadey's coin minions (user, 2026-11-16: "or 2 jade bats"): a carved jade bat with
	/// verdigris wings and a gilt collar (art/bosses/jadey/make_jadey_art.py). Vanilla's bat flight (<c>aiStyle</c> 14 as the
	/// Cave Bat: <c>AIType</c>), its hit lays a stack of the jade curse (my call: all of Jadey's jade bites curse, as her
	/// attacks do). Only ever made by her coins (no natural spawn), two at a time; no loot (<see cref="JadeyMinion"/>).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; T4 like Coghaven): against the Giant Bat's pre-Hardmode cousins
	/// (the Cave Bat, terraria.wiki.gg: 16 life, 2 defense, 13 contact in Classic; the Jungle Bat 34 / 4 / 20): <see cref="Life"/>
	/// life, <see cref="Defense"/> defense, <see cref="ContactDamage"/> contact (halved again as her minion: <see cref="JadeyMinion.LifeScale"/>).</para>
	/// <para>D2: vanilla's AI and its sync; the curse on the hit player's own client (<see cref="JadeCursePlayer"/>). D1: a frame
	/// from the game clock; the eyes' glow drawn added, no allocation.</para>
	/// </summary>
	public class JadeBat : CogpunkNPC
	{
		public const int Life = 80, ContactDamage = 36, Defense = 6;
		public const int FrameTicks = 4;

		private static Asset<Texture2D> glow;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = JadeyRigData.BatFrames;
			glow = Core.Visuals.DepthLayers.RequestOptional(Texture + "_Glow");
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Velocity = 1f });
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			NPC.width = 24;
			NPC.height = 18;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.aiStyle = NPCAIStyleID.Bat;
			AIType = NPCID.CaveBat;
			NPC.noGravity = true;
			NPC.knockBackResist = 0.6f;
			NPC.HitSound = SoundID.NPCHit5;
			NPC.DeathSound = SoundID.Shatter;
			NPC.value = 0f;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		/// <summary>Its bite lays a stack of the jade curse (on the hit player's own client).</summary>
		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			JadeCursePlayer.Hit(target);
		}

		public override void FindFrame(int frameHeight) {
			int frame = (int)((Main.GameUpdateCount / FrameTicks + (uint)NPC.whoAmI) % JadeyRigData.BatFrames);
			NPC.frame.Y = frame * frameHeight;
			NPC.spriteDirection = NPC.velocity.X > 0f ? 1 : -1;      // the art faces left
		}

		/// <summary>Drawn here, the body and then its eyes' glow added on top with the same transform (vanilla's own NPC draw
		/// offsets the frame from the hitbox; this keeps both on the 2 px grid, centred on the hitbox, never rotated: D4).</summary>
		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			Texture2D tex = TextureAssets.Npc[Type].Value;
			Rectangle frame = NPC.frame;
			frame.Height = JadeyRigData.BatHeight;                   // the cell, without the 2 px gap under it
			Vector2 at = NPC.Center - screenPos + new Vector2(0f, NPC.gfxOffY) - new Vector2(frame.Width / 2f, frame.Height / 2f);
			at = new Vector2(Core.Visuals.DepthLayers.Snap(at.X), Core.Visuals.DepthLayers.Snap(at.Y));
			SpriteEffects fx = NPC.spriteDirection == 1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			spriteBatch.Draw(tex, at, frame, NPC.GetAlpha(drawColor), 0f, Vector2.Zero, 1f, fx, 0f);
			if (glow?.IsLoaded == true && !NPC.IsABestiaryIconDummy) {
				spriteBatch.Draw(glow.Value, at, frame, new Color(255, 255, 255, 0) * NPC.Opacity, 0f, Vector2.Zero, 1f, fx, 0f);
			}
			return false;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 2 : 10;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.GemEmerald, out _);
			}
		}
	}
}
