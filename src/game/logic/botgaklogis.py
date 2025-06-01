import random
from ..util import get_direction, position_equals
from game.models import GameObject, Board


class BotGakLogis(object):
  def __init__(self):
    self.goal_position = None
    self.previous_position = (None, None)
    self.turn_direction = 1
    self.SCAN_RADIUS = 2  # Jarak pemindaian dalam blok
    self.RED_DIAMOND_SCORE_MULTIPLIER = 2.0  # Pengali skor untuk redDiamond

  def next_move(self, board_bot: GameObject, board: Board):
    props = board_bot.properties
    current_position = board_bot.position

    # --- FASE 1: Menentukan Tujuan (Goal Setting) ---

    # PRIORITAS 1: Kembali ke markas jika waktu sudah menipis (dan punya berlian)
    # Asumsi: board.time_left dalam milidetik (10 detik = 10000 milidetik)
    if board.time_left < 10000 and props.diamonds > 0:
      self.goal_position = props.base
      if position_equals(current_position, self.goal_position):
        self.goal_position = None

    # PRIORITAS 2: Kembali ke markas jika inventaris penuh (dan sudah sampai markas)
    elif props.diamonds == 5:  # Asumsi kapasitas maksimum berlian adalah 5
      self.goal_position = props.base
      if position_equals(current_position, self.goal_position):
        pass  # Bot diam di markas, menunggu game memproses penyetoran.

    # PRIORITAS 3: Cari berlian (berdasarkan skor bobot)
    else:
      self.goal_position = None  # Reset tujuan sementara

      best_score = -1.0  # Skor tertinggi yang ditemukan
      best_diamond_pos = None  # Posisi diamond dengan skor tertinggi

      # Iterasi semua diamond yang ada di board
      for diamond in board.diamonds:
        space_left = props.inventory_size - props.diamonds

        # Cek apakah diamond bisa diambil dan bukan posisi bot saat ini
        if diamond.properties.points <= space_left and \
          not position_equals(current_position, diamond.position):

          # Hitung jarak Manhattan ke diamond
          dist_x = abs(current_position.x - diamond.position.x)
          dist_y = abs(current_position.y - diamond.position.y)
          distance = dist_x + dist_y

          # Beri bobot lebih pada redDiamond (jika dalam radius atau tidak ada pilihan lain)
          diamond_value = diamond.properties.points

          # Ini adalah bagian inti pembobotan skor
          # Jika diamond adalah 'redDiamond'
          if diamond.properties.type == 'redDiamond':
            diamond_value *= self.RED_DIAMOND_SCORE_MULTIPLIER

          # Hitung skor berdasarkan nilai dan jarak
          # Tambah 1 pada jarak untuk menghindari pembagian dengan nol dan memberi nilai pada diamond terdekat
          current_score = diamond_value / (distance + 1)

          # Jika diamond ini dalam radius, kita mungkin bisa memberi bobot ekstra
          # Anda bisa menambahkan logika bobot ekstra di sini jika perlu,
          # tapi dengan skor berbasis jarak ini, diamond dekat sudah lebih diutamakan.

          # Pilih diamond dengan skor tertinggi
          if current_score > best_score:
            best_score = current_score
            best_diamond_pos = diamond.position

      # Setelah memindai semua diamond yang bisa diambil, tetapkan tujuan
      if best_diamond_pos:
        self.goal_position = best_diamond_pos
      else:
        # Jika tidak ada diamond sama sekali yang bisa diambil
        if props.diamonds > 0:  # Jika punya diamond (tapi tidak penuh) dan tidak bisa ambil lagi, kembali ke markas (opsional)
          self.goal_position = props.base
        else:  # Tidak ada diamond yang bisa diambil dan tidak punya diamond, bot diam
          return 0, 0

          # --- FASE 2: Pergerakan Menuju Tujuan & Penanganan Terjebak ---
    delta_x, delta_y = 0, 0
    if self.goal_position:
      cur_x = current_position.x
      cur_y = current_position.y

      # Gunakan get_direction dari utilitas untuk menghitung langkah ke tujuan
      delta_x, delta_y = get_direction(
        cur_x, cur_y,
        self.goal_position.x, self.goal_position.y,
      )

      # Deteksi dan penanganan bot terjebak
      if (cur_x, cur_y) == self.previous_position:
        if delta_x != 0:
          delta_y = delta_x * self.turn_direction
          delta_x = 0
        elif delta_y != 0:
          delta_x = delta_y * self.turn_direction
          delta_y = 0
        self.turn_direction = -self.turn_direction

        # Penting: Jika terjebak, reset tujuan agar bot cari ulang di giliran berikutnya
        self.goal_position = None

      self.previous_position = (cur_x, cur_y)
      return delta_x, delta_y

    return 0, 0