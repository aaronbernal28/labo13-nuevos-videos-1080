from dataclasses import dataclass
from pathlib import Path


type VideoName = str
type PixelCentroid = tuple[float, float]


@dataclass(frozen=True)
class FrameRecord:
	video_name: VideoName
	frame_index: int
	t_sec: float
	stem: str
	png_path: Path


@dataclass(frozen=True)
class PendulumConstants:
	length_no_base_m: float = 0.737
	length_with_base_m: float = 0.778
	sigma_length_m: float = 0.005
	width_m: float = 0.003
	sigma_caliper_m: float = 0.0002
	sigma_frame_s: float = 1.0 / 59.96

	@property
	def length_cm_m(self) -> float:
		return 0.5 * (self.length_no_base_m + self.length_with_base_m)


@dataclass(frozen=True)
class HarmonicFitResult:
	video_name: VideoName
	damped: bool
	amplitude_rad: float
	sigma_amplitude_rad: float
	gamma_s_inv: float
	sigma_gamma_s_inv: float
	omega_rad_s: float
	sigma_omega_rad_s: float
	phi_rad: float
	sigma_phi_rad: float
	offset_rad: float
	sigma_offset_rad: float
	omega0_rad_s: float
	sigma_omega0_rad_s: float
	period_s: float
	sigma_period_s: float
	chi2: float
	dof: int
	chi2_reduced: float
	p_value: float
	g_cm_m_s2: float
	sigma_g_cm_m_s2: float
