"""Constants for the magnetic-color-wheel ball simulation."""

WINDOW_W = 1200
WINDOW_H = 900

SIDEBAR_W = 320
BOX_MARGIN = 24

# Square sim canvas on the left
SIM_SIZE = min(WINDOW_W - SIDEBAR_W - 3 * BOX_MARGIN, WINDOW_H - 2 * BOX_MARGIN)
SIM_X = BOX_MARGIN
SIM_Y = (WINDOW_H - SIM_SIZE) // 2

BG_COLOR = (0, 0, 0)
WINDOW_BG = (12, 12, 16)
BORDER_COLOR = (210, 210, 220)
BORDER_WIDTH = 2

# Balls
BALL_RADIUS = 6
DEFAULT_N = 200
MIN_N = 5
MAX_N = 1000

# Physics
# Force is back as a slider so it can be tuned by hand. The range goes higher
# now to give more attraction to play with before we lock it to a constant.
DEFAULT_FORCE = 30000.0
MIN_FORCE = 0.0
MAX_FORCE = 120000.0

# Fixed internal damping (1/s exponential). Not user-exposed: it just keeps
# the system stable and lets clusters settle instead of flying forever.
DAMPING = 1.4

SOFTENING = 100.0   # px^2 floor inside 1/r^2 to avoid singularity
MAX_SPEED = 700.0   # px/s safety cap

FPS = 60

# Distributions
DISTRIBUTIONS = ["Uniform", "Gaussian", "Bimodal"]
DEFAULT_DISTRIBUTION = "Uniform"

GAUSS_DEFAULT_MEAN = 0.5
GAUSS_DEFAULT_STD = 0.10
BIMO_DEFAULT_CENTER = 0.0
BIMO_DEFAULT_STD = 0.05
