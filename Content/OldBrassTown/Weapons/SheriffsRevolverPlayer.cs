using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Weapons
{
	/// <summary>
	/// The Sheriff's Revolver's cylinder (user-set 2026-11-04: "it should need to reload after 6 shots taking 1.5 seconds;
	/// keep track of the shots so it does not reset if the player swaps weapons to exploit it"): the rounds left live on the
	/// player, not on the item, so putting the gun away and drawing it again changes nothing; the reload starts the moment
	/// the last round is fired and runs to its end whatever the player holds (it can't be cut short or restarted). A death
	/// leaves a full cylinder, as a respawn leaves full mana.
	/// <para>D2: the owner's (only the owner shoots); nothing else needs it. D1: two ints.</para>
	/// </summary>
	public sealed class SheriffsRevolverPlayer : ModPlayer
	{
		public const int Chambers = 6;                          // user-set
		public const int ReloadTicks = 90;                      // 1.5 s (user-set)

		/// <summary>Rounds left in the cylinder (0 while reloading).</summary>
		public int Rounds { get; private set; } = Chambers;

		/// <summary>Ticks of reload left (0 when loaded).</summary>
		public int Reload { get; private set; }

		public bool Reloading => Reload > 0;

		/// <summary>0..1 how far the reload has gone (for the cylinder shown by the player).</summary>
		public float ReloadProgress => Reloading ? 1f - Reload / (float)ReloadTicks : 1f;

		public override void Initialize() {
			Rounds = Chambers;
			Reload = 0;
		}

		/// <summary>Owner: one round fired; the last one starts the reload.</summary>
		public void Fired() {
			if (Rounds > 0) {
				Rounds--;
			}
			if (Rounds == 0 && Reload == 0) {
				Reload = ReloadTicks;
				if (!Main.dedServ && Player.whoAmI == Main.myPlayer) {
					SoundEngine.PlaySound(SoundID.Unlock with { Pitch = -0.3f, Volume = 0.7f }, Player.Center);   // the cylinder swings out
				}
			}
		}

		public override void PostUpdate() {
			if (Reload <= 0) {
				return;
			}
			Reload--;
			if (!Main.dedServ && Player.whoAmI == Main.myPlayer && Reload % 15 == 7 && Reload > 0) {
				SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.2f, Volume = 0.6f }, Player.Center);   // a round in
			}
			if (Reload == 0) {
				Rounds = Chambers;
				if (!Main.dedServ && Player.whoAmI == Main.myPlayer) {
					SoundEngine.PlaySound(SoundID.Unlock with { Pitch = 0.3f, Volume = 0.8f }, Player.Center);    // snapped shut
				}
			}
		}

		public override void OnRespawn() {
			Rounds = Chambers;
			Reload = 0;
		}
	}
}
