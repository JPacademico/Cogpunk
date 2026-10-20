using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Core.Templates
{
	/// <summary>
	/// Base for enemies and bosses driven by a server-authoritative state machine (D2).
	/// <para><c>NPC.ai[0]</c> = state and <c>NPC.ai[1]</c> = timer, both synced by vanilla. <c>ai[2]</c> and
	/// <c>ai[3]</c> are free for subclasses. <c>localAI[]</c> is not synced: use it for visuals only.</para>
	/// <para>Subclasses implement <see cref="UpdateState"/>. Only the server (or singleplayer) changes
	/// state, through <see cref="ChangeState"/>; clients follow the synced <c>ai[]</c>.</para>
	/// </summary>
	public abstract class StateMachineNPC : CogpunkNPC
	{
		protected int State {
			get => (int)NPC.ai[0];
			private set => NPC.ai[0] = value;
		}

		protected ref float Timer => ref NPC.ai[1];

		/// <summary>True on the side allowed to make gameplay decisions (server or singleplayer).</summary>
		protected static bool IsAuthority => Main.netMode != NetmodeID.MultiplayerClient;

		public sealed override void AI() {
			Timer++;
			UpdateState();
			GuardAgainstNaN();
		}

		/// <summary>Called every tick on every side. Keep it allocation-free (D1).</summary>
		protected abstract void UpdateState();

		/// <summary>Switches state and resets the timer. Ignored on multiplayer clients. Syncs only on change.</summary>
		protected void ChangeState(int next) {
			if (!IsAuthority) {
				return;
			}
			State = next;
			Timer = 0f;
			NPC.netUpdate = true;
		}

		// A NaN velocity/position (usually from normalizing a zero vector) makes the NPC vanish or breaks
		// drawing and collision. Recover instead of letting it spread (D0).
		private void GuardAgainstNaN() {
			if (MathSafety.Sanitize(ref NPC.velocity)) {
				SafeLog.Warn("NPC.NaNVelocity:" + Name, "{0} produced a NaN velocity; reset to zero.", Name);
				NPC.netUpdate = IsAuthority;
			}
			if (!MathSafety.IsFinite(NPC.position)) {
				SafeLog.Warn("NPC.NaNPosition:" + Name, "{0} produced a NaN position; despawned.", Name);
				if (IsAuthority) {
					NPC.active = false;
					NPC.netUpdate = true;
				}
				else if (MathSafety.IsFinite(NPC.oldPosition)) {
					NPC.position = NPC.oldPosition;
				}
			}
		}
	}
}
