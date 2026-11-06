/**
 * Dataset Domain and Sector Definitions.
 */

export type SectorType = "Agriculture" | "Education" | "Health and Demographics" | "Rural Development";

export interface DatasetItem {
  id: string;
  name: string;
  tableName: string;
  sector: SectorType;
  description: string;
  rowCount?: number;
  columnsCount?: number;
  columns?: Array<{ name: string; type: string }>;
  isAvailable: boolean;
}

export const KNOWN_SECTOR_MAPPINGS: Record<string, SectorType> = {
  // Agriculture
  ndap_pm_kisan_disbursement: "Agriculture",
  ndap_crop_production_census: "Agriculture",
  ndap_mandi_commodity_prices: "Agriculture",
  ndap_fertilizer_distribution: "Agriculture",
  ndap_soil_health_records: "Agriculture",

  // Education
  ndap_education_stats: "Education",
  ndap_school_infrastructure: "Education",
  ndap_higher_education_aishe: "Education",
  ndap_midday_meal_scheme: "Education",
  ndap_vocational_skill_training: "Education",

  // Health and Demographics
  ndap_nfhs5_health_indicators: "Health and Demographics",
  ndap_rural_health_infrastructure: "Health and Demographics",
  ndap_maternal_child_mortality: "Health and Demographics",
  ndap_ayushman_bharat_pmjay: "Health and Demographics",
  ndap_national_tuberculosis_portal: "Health and Demographics",

  // Rural Development
  mgnrega_state_annual_employment: "Rural Development",
  ndap_pmgsy_rural_roads: "Rural Development",
  ndap_jal_jeevan_tap_water: "Rural Development",
  ndap_pmay_rural_housing: "Rural Development",
  ndap_gram_panchayat_finance: "Rural Development",
};

