using System;
using System.Collections.Generic;
using System.IO;
using Cogpunk.Content.Junkyard.Map;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.UI;

namespace Cogpunk.Content.Research.Items
{
	/// <summary>
	/// Clump scanner, player state, multiplayer packets, compass arrow layer, and icon-picker UI for <see cref="OreGps"/>.
	/// <list type="bullet">
	/// <item><b>D0</b>: every tile check goes through <see cref="TileSafety.TryGetTile"/>; the 6-tile clump BFS uses a
	/// stack-allocated 6-slot buffer (zero heap allocation, at most 48 neighbor reads per matching tile); shell scan is bounded
	/// by <see cref="MaxSearchRadius"/>; packet player/target/coordinate values are validated.</item>
	/// <item><b>D1</b>: scans run only on selection and every <see cref="RescanIntervalTicks"/> ticks while tracking; arrow
	/// drawing reuses the cached Mysterious Map arrow sheets with zero allocations.</item>
	/// <item><b>D2</b>: in multiplayer, the server owns the full world tile map and answers <see cref="OreGpsRequestPacket"/>
	/// with <see cref="OreGpsTargetPacket"/> so veins outside streamed client sections are still found accurately.</item>
	/// </list>
	/// </summary>
	public sealed class OreGpsSystem : ModSystem
	{
		public readonly struct TargetEntry
		{
			public readonly int ItemType;
			public readonly int TileType;
			public readonly int ExposedGemStyle;
			public readonly bool IsGem;

			public TargetEntry(int itemType, int tileType, bool isGem = false, int exposedGemStyle = -1) {
				ItemType = itemType;
				TileType = tileType;
				IsGem = isGem;
				ExposedGemStyle = exposedGemStyle;
			}
		}

		public const int MinClumpSize = OreGps.MinClumpBlocks;
		public const int MaxSearchRadius = 900;
		public const int RescanIntervalTicks = 75;
		public const int ServerRequestCooldown = 25;

		public static TargetEntry[] Targets { get; private set; } = Array.Empty<TargetEntry>();

		public override void PostSetupContent() {
			Targets = new[] {
				// Row 1: Pre-Hardmode Ores
				new TargetEntry(ItemID.CopperOre, TileID.Copper),
				new TargetEntry(ItemID.TinOre, TileID.Tin),
				new TargetEntry(ItemID.IronOre, TileID.Iron),
				new TargetEntry(ItemID.LeadOre, TileID.Lead),
				new TargetEntry(ItemID.SilverOre, TileID.Silver),
				new TargetEntry(ItemID.TungstenOre, TileID.Tungsten),
				new TargetEntry(ItemID.GoldOre, TileID.Gold),
				new TargetEntry(ItemID.PlatinumOre, TileID.Platinum),
				new TargetEntry(ItemID.DemoniteOre, TileID.Demonite),
				new TargetEntry(ItemID.CrimtaneOre, TileID.Crimtane),
				new TargetEntry(ItemID.Meteorite, TileID.Meteorite),
				new TargetEntry(ItemID.Hellstone, TileID.Hellstone),
				new TargetEntry(ModContent.ItemType<OldBrassTown.Items.TarnishedBrassOre>(), ModContent.TileType<OldBrassTown.Tiles.TarnishedBrassOreTile>()),
				// Row 2: Gems (vanilla's seven + Jade)
				new TargetEntry(ItemID.Amethyst, TileID.Amethyst, isGem: true, exposedGemStyle: 0),
				new TargetEntry(ItemID.Topaz, TileID.Topaz, isGem: true, exposedGemStyle: 1),
				new TargetEntry(ItemID.Sapphire, TileID.Sapphire, isGem: true, exposedGemStyle: 2),
				new TargetEntry(ItemID.Emerald, TileID.Emerald, isGem: true, exposedGemStyle: 3),
				new TargetEntry(ItemID.Ruby, TileID.Ruby, isGem: true, exposedGemStyle: 4),
				new TargetEntry(ItemID.Diamond, TileID.Diamond, isGem: true, exposedGemStyle: 5),
				new TargetEntry(ItemID.Amber, TileID.AmberStoneBlock, isGem: true, exposedGemStyle: 6),
				new TargetEntry(ModContent.ItemType<Gems.Items.Jade>(), ModContent.TileType<Gems.Tiles.JadeTile>(), isGem: true),
			};
		}

		public override void Unload() {
			Targets = Array.Empty<TargetEntry>();
		}

		public static bool Matches(Tile tile, in TargetEntry entry) {
			if (!tile.HasTile || tile.IsActuated) {
				return false;
			}
			if (tile.TileType == entry.TileType) {
				return true;
			}
			return entry.ExposedGemStyle >= 0 && tile.TileType == TileID.ExposedGems && tile.TileFrameX / 18 == entry.ExposedGemStyle;
		}

		/// <summary>Finds the Euclidean-nearest 8-connected clump of at least <see cref="MinClumpSize"/> matching tiles within
		/// <see cref="MaxSearchRadius"/> tiles of <paramref name="origin"/>.</summary>
		public static bool FindNearestClump(Point origin, int targetIndex, out Point clumpCenter) {
			clumpCenter = default;
			if (targetIndex < 0 || targetIndex >= Targets.Length) {
				return false;
			}
			TargetEntry entry = Targets[targetIndex];
			long bestDistSq = long.MaxValue;
			Point best = default;

			for (int r = 0; r <= MaxSearchRadius; r++) {
				if (bestDistSq < long.MaxValue && (long)r * r > bestDistSq) {
					break;                                        // no outer shell can beat bestDistSq
				}
				if (r == 0) {
					TryCandidate(origin.X, origin.Y, origin, in entry, ref bestDistSq, ref best);
					continue;
				}
				int x0 = origin.X - r, x1 = origin.X + r;
				int y0 = origin.Y - r, y1 = origin.Y + r;
				for (int x = x0; x <= x1; x++) {
					TryCandidate(x, y0, origin, in entry, ref bestDistSq, ref best);
					TryCandidate(x, y1, origin, in entry, ref bestDistSq, ref best);
				}
				for (int y = y0 + 1; y < y1; y++) {
					TryCandidate(x0, y, origin, in entry, ref bestDistSq, ref best);
					TryCandidate(x1, y, origin, in entry, ref bestDistSq, ref best);
				}
			}

			if (bestDistSq == long.MaxValue) {
				return false;
			}
			clumpCenter = best;
			return true;
		}

		private static void TryCandidate(int x, int y, Point origin, in TargetEntry entry, ref long bestDistSq, ref Point best) {
			long dx = x - origin.X, dy = y - origin.Y;
			long d2 = dx * dx + dy * dy;
			if (d2 >= bestDistSq || !TileSafety.TryGetTile(x, y, out Tile tile) || !Matches(tile, in entry)) {
				return;
			}
			if (IsClumpAt(x, y, in entry, out Point center)) {
				long cdx = center.X - origin.X, cdy = center.Y - origin.Y;
				long cd2 = cdx * cdx + cdy * cdy;
				if (cd2 < bestDistSq) {
					bestDistSq = cd2;
					best = center;
				}
			}
		}

		/// <summary>Zero-allocation bounded BFS stopping at <see cref="MinClumpSize"/> connected tiles.</summary>
		public static bool IsClumpAt(int startX, int startY, in TargetEntry entry, out Point center) {
			Span<Point> queue = stackalloc Point[MinClumpSize];
			queue[0] = new Point(startX, startY);
			int count = 1, head = 0;
			while (head < count && count < MinClumpSize) {
				Point cur = queue[head++];
				for (int oy = -1; oy <= 1 && count < MinClumpSize; oy++) {
					for (int ox = -1; ox <= 1 && count < MinClumpSize; ox++) {
						if (ox == 0 && oy == 0) {
							continue;
						}
						int nx = cur.X + ox, ny = cur.Y + oy;
						if (!TileSafety.TryGetTile(nx, ny, out Tile nt) || !Matches(nt, in entry)) {
							continue;
						}
						bool seen = false;
						for (int k = 0; k < count; k++) {
							if (queue[k].X == nx && queue[k].Y == ny) {
								seen = true;
								break;
							}
						}
						if (!seen) {
							queue[count++] = new Point(nx, ny);
						}
					}
				}
			}
			if (count < MinClumpSize) {
				center = default;
				return false;
			}
			int sumX = 0, sumY = 0;
			for (int k = 0; k < count; k++) {
				sumX += queue[k].X;
				sumY += queue[k].Y;
			}
			center = new Point(sumX / count, sumY / count);
			return true;
		}
	}

	public sealed class OreGpsPlayer : ModPlayer
	{
		public int SelectedIndex = -1;
		public bool HasTarget;
		public Point TargetTile;
		private int rescanTimer;
		public int LastServerScanTick = -1000;

		public override void Initialize() {
			SelectedIndex = -1;
			HasTarget = false;
			TargetTile = default;
			rescanTimer = 0;
			LastServerScanTick = -1000;
		}

		public bool CarriesGps() {
			int gpsType = ModContent.ItemType<OreGps>();
			if (Player.HeldItem?.type == gpsType) {
				return true;
			}
			for (int i = 0; i < Player.inventory.Length; i++) {
				if (Player.inventory[i]?.type == gpsType && Player.inventory[i].stack > 0) {
					return true;
				}
			}
			return false;
		}

		public void Select(int index, bool announce) {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			if (index < 0 || index >= OreGpsSystem.Targets.Length) {
				SelectedIndex = -1;
				HasTarget = false;
				if (Main.netMode == NetmodeID.MultiplayerClient) {
					ModContent.GetInstance<OreGpsRequestPacket>().Send(-1);
				}
				if (announce && !Main.dedServ) {
					Main.NewText(Language.GetTextValue("Mods.Cogpunk.Items.OreGps.Cleared"), new Color(184, 138, 51));
				}
				return;
			}
			SelectedIndex = index;
			rescanTimer = 0;
			RequestScan(announce);
		}

		private bool pendingAnnounce;

		public void RequestScan(bool announce) {
			pendingAnnounce |= announce;
			if (Main.netMode == NetmodeID.SinglePlayer) {
				Point origin = Player.Center.ToTileCoordinates();
				bool found = OreGpsSystem.FindNearestClump(origin, SelectedIndex, out Point center);
				ApplyTarget(SelectedIndex, found, center);
			}
			else if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<OreGpsRequestPacket>().Send(SelectedIndex);
			}
		}

		public void ApplyTarget(int index, bool found, Point center) {
			SelectedIndex = index;
			HasTarget = found && index >= 0 && index < OreGpsSystem.Targets.Length;
			TargetTile = HasTarget ? center : default;
			if (Player.whoAmI == Main.myPlayer && pendingAnnounce && !Main.dedServ && index >= 0 && index < OreGpsSystem.Targets.Length) {
				pendingAnnounce = false;
				string name = Lang.GetItemNameValue(OreGpsSystem.Targets[index].ItemType);
				Main.NewText(HasTarget
					? Language.GetTextValue("Mods.Cogpunk.Items.OreGps.FoundChat", name)
					: Language.GetTextValue("Mods.Cogpunk.Items.OreGps.MissingChat", name, OreGps.MinClumpBlocks),
					HasTarget ? new Color(140, 228, 88) : new Color(236, 122, 88));
			}
		}

		public override void PostUpdate() {
			if (Player.whoAmI != Main.myPlayer || Main.dedServ || SelectedIndex < 0) {
				return;
			}
			if (!CarriesGps()) {
				return;
			}
			if (++rescanTimer >= OreGpsSystem.RescanIntervalTicks) {
				rescanTimer = 0;
				RequestScan(announce: false);
			}
		}
	}

	/// <summary>Client -> server: scan for <c>targetIndex</c> (-1 clears tracking).</summary>
	public sealed class OreGpsRequestPacket : CogpunkPacket
	{
		public void Send(int targetIndex) {
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				return;
			}
			ModPacket p = Begin();
			p.Write((sbyte)Math.Clamp(targetIndex, -1, 120));
			p.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			int index = reader.ReadSByte();
			if (Main.netMode != NetmodeID.Server || sender < 0 || sender >= Main.maxPlayers) {
				return;
			}
			Player player = Main.player[sender];
			if (player == null || !player.active) {
				return;
			}
			OreGpsPlayer gps = player.GetModPlayer<OreGpsPlayer>();
			if (index < 0 || index >= OreGpsSystem.Targets.Length) {
				gps.SelectedIndex = -1;
				gps.HasTarget = false;
				ModContent.GetInstance<OreGpsTargetPacket>().Send(sender, -1, false, default);
				return;
			}
			int now = (int)Main.GameUpdateCount;
			if (now - gps.LastServerScanTick < OreGpsSystem.ServerRequestCooldown) {
				return;
			}
			gps.LastServerScanTick = now;
			bool found = OreGpsSystem.FindNearestClump(player.Center.ToTileCoordinates(), index, out Point center);
			gps.ApplyTarget(index, found, center);
			ModContent.GetInstance<OreGpsTargetPacket>().Send(sender, index, found, center);
		}
	}

	/// <summary>Server -> all clients: synced Ore GPS target for <c>player</c>.</summary>
	public sealed class OreGpsTargetPacket : CogpunkPacket
	{
		public void Send(int player, int index, bool found, Point tile) {
			if (Main.netMode != NetmodeID.Server) {
				return;
			}
			ModPacket p = Begin();
			p.Write((byte)player);
			p.Write((sbyte)index);
			p.Write(found);
			p.Write((short)Math.Clamp(tile.X, 0, short.MaxValue));
			p.Write((short)Math.Clamp(tile.Y, 0, short.MaxValue));
			p.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			int player = reader.ReadByte();
			int index = reader.ReadSByte();
			bool found = reader.ReadBoolean();
			int x = reader.ReadInt16();
			int y = reader.ReadInt16();
			if (Main.netMode != NetmodeID.MultiplayerClient || player < 0 || player >= Main.maxPlayers) {
				return;
			}
			Player pl = Main.player[player];
			if (pl == null || !pl.active) {
				return;
			}
			bool validTile = found && TileSafety.InWorld(x, y);
			pl.GetModPlayer<OreGpsPlayer>().ApplyTarget(index, validTile, validTile ? new Point(x, y) : default);
		}
	}

	/// <summary>
	/// Draws the Mysterious Map's pre-rendered 16-heading compass arrow around a player tracking an ore/gem clump with
	/// <see cref="OreGps"/>, plus a tiny icon of the tracked mineral beside it.
	/// </summary>
	public sealed class OreGpsArrowLayer : PlayerDrawLayer
	{
		private const float NearDistance = 45f * 16f;
		private static Asset<Texture2D> arrow, glow;
		private static int mapType = -1;

		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			const string path = "Cogpunk/Content/Junkyard/Map/MysteriousMapArrow";
			arrow = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
			glow = ModContent.HasAsset(path + "_Glow") ? ModContent.Request<Texture2D>(path + "_Glow") : null;
		}

		public override void Unload() {
			arrow = glow = null;
			mapType = -1;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.FrontAccFront);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (mapType < 0) {
				mapType = ModContent.ItemType<MysteriousMap>();
			}
			Player player = drawInfo.drawPlayer;
			if (drawInfo.shadow != 0f || player.dead || player.ghost || player.HeldItem.type == mapType) {
				return false;
			}
			OreGpsPlayer gps = player.GetModPlayer<OreGpsPlayer>();
			return gps.HasTarget && gps.SelectedIndex >= 0 && gps.SelectedIndex < OreGpsSystem.Targets.Length && gps.CarriesGps();
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (arrow?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			OreGpsPlayer gps = player.GetModPlayer<OreGpsPlayer>();
			Vector2 centre = player.MountedCenter;
			Vector2 toTarget = gps.TargetTile.ToWorldCoordinates() - centre;
			float distance = toTarget.Length();
			float angle = distance > 1f ? MathF.Atan2(toTarget.Y, toTarget.X) : MathHelper.PiOver2;
			int dirs = MysteriousMapArrowLayer.Directions;
			int heading = ((int)MathF.Round(angle / MathHelper.TwoPi * dirs) % dirs + dirs) % dirs;
			float snapped = heading * MathHelper.TwoPi / dirs;
			Vector2 world = centre + new Vector2(MathF.Cos(snapped), MathF.Sin(snapped)) * MysteriousMapArrowLayer.Radius;
			Vector2 at = world - Main.screenPosition;
			int fs = MysteriousMapArrowLayer.FrameSize;
			Vector2 position = new(MathF.Round(at.X - fs * 0.5f), MathF.Round(at.Y - fs * 0.5f + player.gfxOffY));
			Rectangle source = new(0, heading * MysteriousMapArrowLayer.FrameStride, fs, fs);
			Color light = Lighting.GetColor(world.ToTileCoordinates());
			drawInfo.DrawDataCache.Add(new DrawData(arrow.Value, position, source, Color.Lerp(light, Color.White, 0.45f)));
			if (glow?.IsLoaded == true) {
				float speed = distance < NearDistance ? 9f : 3f;
				float pulse = 0.6f + 0.4f * MathF.Sin(Main.GlobalTimeWrappedHourly * speed);
				drawInfo.DrawDataCache.Add(new DrawData(glow.Value, position, source, Color.White * pulse));
			}
		}
	}

	/// <summary>
	/// Lightweight Cogpunk brass-and-slate icon picker UI for <see cref="OreGps"/>: row 1 shows pre-Hardmode ores, row 2 shows
	/// gems (vanilla's seven + Jade), with item icons, hover tooltips, and an Off button.
	/// </summary>
	[Autoload(Side = ModSide.Client)]
	public sealed class OreGpsUISystem : ModSystem
	{
		private static bool open;
		private static Item[] iconSamples;

		private static readonly Color Rim = new(21, 22, 28), Brass = new(184, 138, 51), BrassLight = new(223, 185, 78),
			Field = new(24, 20, 36), SlotBg = new(34, 30, 50), SelectedRim = new(140, 228, 88);

		public static void Toggle() {
			open = !open;
			SoundEngine.PlaySound(open ? SoundID.MenuOpen : SoundID.MenuClose);
		}

		public override void ClearWorld() {
			open = false;
		}

		public override void Unload() {
			open = false;
			iconSamples = null;
		}

		public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers) {
			if (!open) {
				return;
			}
			int index = layers.FindIndex(static l => l.Name == "Vanilla: Inventory");
			if (index < 0) {
				return;
			}
			layers.Insert(index + 1, new LegacyGameInterfaceLayer("Cogpunk: Ore GPS", DrawPopup, InterfaceScaleType.UI));
		}

		private static bool DrawPopup() {
			Player player = Main.LocalPlayer;
			if (player == null || !player.active || player.dead || Main.ingameOptionsWindow || Main.inFancyUI) {
				open = false;
				return true;
			}
			var targets = OreGpsSystem.Targets;
			if (targets.Length == 0) {
				return true;
			}
			if (iconSamples == null || iconSamples.Length != targets.Length) {
				iconSamples = new Item[targets.Length];
				for (int i = 0; i < targets.Length; i++) {
					iconSamples[i] = new Item(targets[i].ItemType);
				}
			}

			int oreCount = 0, gemCount = 0;
			for (int i = 0; i < targets.Length; i++) {
				if (targets[i].IsGem) {
					gemCount++;
				}
				else {
					oreCount++;
				}
			}
			const int cell = 38, gap = 4, pad = 14;
			int cols = Math.Max(oreCount, gemCount + 1);
			int panelW = pad * 2 + cols * cell + (cols - 1) * gap;
			int panelH = 148;
			Rectangle panel = new((Main.screenWidth - panelW) / 2, (int)(Main.screenHeight * 0.28f), panelW, panelH);

			SpriteBatch sb = Main.spriteBatch;
			Texture2D px = TextureAssets.MagicPixel.Value;
			Point mouse = Main.MouseScreen.ToPoint();
			bool inside = panel.Contains(mouse);
			if (inside) {
				player.mouseInterface = true;
			}

			DrawBox(sb, px, panel, Field, Brass);
			string title = Language.GetTextValue("Mods.Cogpunk.Items.OreGps.MenuTitle");
			Utils.DrawBorderString(sb, title, new Vector2(panel.Center.X, panel.Y + 18f), BrassLight, 0.9f, 0.5f, 0.5f);

			OreGpsPlayer gps = player.GetModPlayer<OreGpsPlayer>();
			string hoverText = null;
			int clickedIndex = -2;

			int oreIdx = 0, gemIdx = 0;
			for (int i = 0; i < targets.Length; i++) {
				bool gem = targets[i].IsGem;
				int col = gem ? gemIdx++ : oreIdx++;
				int rowY = panel.Y + (gem ? 92 : 42);
				int rowCount = gem ? gemCount + 1 : oreCount;
				int rowStartX = panel.X + (panelW - (rowCount * cell + (rowCount - 1) * gap)) / 2;
				Rectangle slot = new(rowStartX + col * (cell + gap), rowY, cell, cell);

				bool over = slot.Contains(mouse);
				bool selected = gps.SelectedIndex == i;
				Color border = selected ? SelectedRim : over ? BrassLight : new Color(79, 85, 98);
				DrawBox(sb, px, slot, SlotBg, border);
				ItemSlot.DrawItemIcon(iconSamples[i], ItemSlot.Context.InventoryItem, sb, slot.Center.ToVector2(), 1f, 28f, Color.White);
				if (over) {
					hoverText = Lang.GetItemNameValue(targets[i].ItemType);
					if (Main.mouseLeft && Main.mouseLeftRelease) {
						clickedIndex = selected ? -1 : i;
					}
				}
			}

			// "Off" button at the end of the gem row
			{
				int rowCount = gemCount + 1;
				int rowStartX = panel.X + (panelW - (rowCount * cell + (rowCount - 1) * gap)) / 2;
				Rectangle offSlot = new(rowStartX + gemCount * (cell + gap), panel.Y + 92, cell, cell);
				bool over = offSlot.Contains(mouse);
				DrawBox(sb, px, offSlot, SlotBg, over ? new Color(236, 122, 88) : new Color(79, 85, 98));
				Utils.DrawBorderString(sb, "X", offSlot.Center.ToVector2() + new Vector2(0f, 3f), new Color(236, 122, 88), 0.85f, 0.5f, 0.5f);
				if (over) {
					hoverText = Language.GetTextValue("Mods.Cogpunk.Items.OreGps.TurnOff");
					if (Main.mouseLeft && Main.mouseLeftRelease) {
						clickedIndex = -1;
					}
				}
			}

			if (clickedIndex >= -1) {
				Main.mouseLeftRelease = false;
				SoundEngine.PlaySound(SoundID.MenuTick);
				gps.Select(clickedIndex, announce: true);
				open = false;
			}
			else if (Main.mouseLeft && Main.mouseLeftRelease && !inside && player.itemAnimation <= 0) {
				open = false;
			}

			if (hoverText != null) {
				Main.instance.MouseText(hoverText);
			}
			return true;
		}

		private static void DrawBox(SpriteBatch sb, Texture2D px, Rectangle r, Color fill, Color border) {
			sb.Draw(px, r, Rim);
			sb.Draw(px, new Rectangle(r.X + 2, r.Y + 2, r.Width - 4, r.Height - 4), border);
			sb.Draw(px, new Rectangle(r.X + 4, r.Y + 4, r.Width - 8, r.Height - 8), fill);
		}
	}
}
