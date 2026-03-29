export const vendors = {
  tsmc: {
    id: 'tsmc',
    name: 'TSMC',
    ticker: 'TSM',
    industry: 'Semiconductors',
    hq: 'Taiwan',
    overallRiskScore: 78,
    riskLevel: 'High',
    dependencyExposure: 84,

    riskTrend: [
      { month: 'Apr', score: 62 },
      { month: 'May', score: 65 },
      { month: 'Jun', score: 68 },
      { month: 'Jul', score: 71 },
      { month: 'Aug', score: 69 },
      { month: 'Sep', score: 74 },
      { month: 'Oct', score: 72 },
      { month: 'Nov', score: 75 },
      { month: 'Dec', score: 77 },
      { month: 'Jan', score: 76 },
      { month: 'Feb', score: 79 },
      { month: 'Mar', score: 78 },
    ],

    industryExposure: [
      { industry: 'Rare Earth Mining',      tier: 'T3', exposure: 38, riskLevel: 'High' },
      { industry: 'Chemical Processing',    tier: 'T2', exposure: 27, riskLevel: 'High' },
      { industry: 'Precision Equipment',    tier: 'T2', exposure: 19, riskLevel: 'Medium' },
      { industry: 'Energy & Utilities',     tier: 'T3', exposure: 10, riskLevel: 'Medium' },
      { industry: 'Logistics & Freight',    tier: 'T2', exposure:  6, riskLevel: 'Low' },
    ],

    tierSplit: { tier2: 42, tier3: 58 },

    riskDimensions: [
      { dimension: 'Geography', tier2: 74, tier3: 88 },
      { dimension: 'Industry',  tier2: 68, tier3: 82 },
      { dimension: 'Logistics', tier2: 55, tier3: 71 },
    ],

    insights: [
      {
        id: 1,
        layer: 'Tier-3',
        dimension: 'Geography',
        severity: 'high',
        text: 'Tier-3 risk is primarily driven by geographic concentration in East Asia, with ~73% of inferred upstream inputs originating from Taiwan, China, and South Korea.',
      },
      {
        id: 2,
        layer: 'Tier-2',
        dimension: 'Industry',
        severity: 'high',
        text: 'Tier-2 chemical processing suppliers show high single-source dependency on APAC-based raw material producers, creating potential amplification risk.',
      },
      {
        id: 3,
        layer: 'Tier-3',
        dimension: 'Logistics',
        severity: 'med',
        text: 'Rare earth mining routes through the South China Sea introduce concentrated freight risk, particularly in periods of geopolitical tension.',
      },
    ],

    forecast: [
      { period: 'Mar', actual: 78,   forecast: null, upper: null, lower: null },
      { period: 'Apr', actual: null, forecast: 80,   upper: 84,   lower: 76 },
      { period: 'May', actual: null, forecast: 82,   upper: 87,   lower: 77 },
      { period: 'Jun', actual: null, forecast: 85,   upper: 91,   lower: 79 },
      { period: 'Jul', actual: null, forecast: 84,   upper: 90,   lower: 78 },
      { period: 'Aug', actual: null, forecast: 86,   upper: 93,   lower: 79 },
    ],

    leadingIndicators: [
      { signal: 'Geopolitical Tension Index',       value: '8.4 / 10',       trend: 'up',     severity: 'high' },
      { signal: 'Rare Earth Export Controls',       value: '+34% YoY',        trend: 'up',     severity: 'high' },
      { signal: 'APAC Freight Congestion',          value: '6.1 / 10',       trend: 'up',     severity: 'med'  },
      { signal: 'Chemical Input Price Volatility',  value: '+18% QoQ',        trend: 'up',     severity: 'med'  },
      { signal: 'Supplier Concentration Score',     value: '0.82 HHI',        trend: 'stable', severity: 'high' },
    ],

    riskDirection: 'Increasing',

    radarDimensions: {
      geography:    88,
      industry:     78,
      logistics:    71,
      concentration: 84,
      volatility:   76,
      fragility:    78,
    },
  },

  foxconn: {
    id: 'foxconn',
    name: 'Foxconn',
    ticker: 'HNHPF',
    industry: 'Electronics Mfg',
    hq: 'Taiwan',
    overallRiskScore: 65,
    riskLevel: 'Medium',
    dependencyExposure: 71,

    riskTrend: [
      { month: 'Apr', score: 58 },
      { month: 'May', score: 60 },
      { month: 'Jun', score: 61 },
      { month: 'Jul', score: 64 },
      { month: 'Aug', score: 63 },
      { month: 'Sep', score: 66 },
      { month: 'Oct', score: 67 },
      { month: 'Nov', score: 65 },
      { month: 'Dec', score: 64 },
      { month: 'Jan', score: 66 },
      { month: 'Feb', score: 65 },
      { month: 'Mar', score: 65 },
    ],

    industryExposure: [
      { industry: 'Semiconductor Components', tier: 'T2', exposure: 35, riskLevel: 'High' },
      { industry: 'PCB Manufacturing',        tier: 'T2', exposure: 24, riskLevel: 'Medium' },
      { industry: 'Rare Earth Mining',        tier: 'T3', exposure: 21, riskLevel: 'High' },
      { industry: 'Plastics & Polymers',      tier: 'T3', exposure: 12, riskLevel: 'Medium' },
      { industry: 'Logistics & Freight',      tier: 'T2', exposure:  8, riskLevel: 'Low' },
    ],

    tierSplit: { tier2: 55, tier3: 45 },

    riskDimensions: [
      { dimension: 'Geography', tier2: 68, tier3: 74 },
      { dimension: 'Industry',  tier2: 72, tier3: 64 },
      { dimension: 'Logistics', tier2: 61, tier3: 55 },
    ],

    insights: [
      {
        id: 1,
        layer: 'Tier-2',
        dimension: 'Industry',
        severity: 'high',
        text: 'Tier-2 semiconductor component sourcing is concentrated among a small cluster of APAC manufacturers, creating amplified risk during supply crunches.',
      },
      {
        id: 2,
        layer: 'Tier-3',
        dimension: 'Geography',
        severity: 'med',
        text: 'Tier-3 rare earth dependencies trace back to a narrow set of mining regions in Inner Mongolia and the DRC, adding geographic fragility.',
      },
      {
        id: 3,
        layer: 'Tier-2',
        dimension: 'Logistics',
        severity: 'med',
        text: 'Dual port dependency on Shenzhen and Kaohsiung introduces a choke-point risk under logistics stress scenarios.',
      },
    ],

    forecast: [
      { period: 'Mar', actual: 65,   forecast: null, upper: null, lower: null },
      { period: 'Apr', actual: null, forecast: 66,   upper: 70,   lower: 62 },
      { period: 'May', actual: null, forecast: 67,   upper: 72,   lower: 62 },
      { period: 'Jun', actual: null, forecast: 68,   upper: 73,   lower: 63 },
      { period: 'Jul', actual: null, forecast: 67,   upper: 72,   lower: 62 },
      { period: 'Aug', actual: null, forecast: 69,   upper: 74,   lower: 64 },
    ],

    leadingIndicators: [
      { signal: 'APAC Manufacturing PMI',       value: '48.2 (contraction)', trend: 'down',   severity: 'med'  },
      { signal: 'Semiconductor Lead Times',     value: '+12 weeks',          trend: 'up',     severity: 'high' },
      { signal: 'PCB Input Cost Index',         value: '+9% QoQ',            trend: 'up',     severity: 'med'  },
      { signal: 'Port Congestion (Shenzhen)',   value: '5.8 / 10',          trend: 'stable', severity: 'med'  },
      { signal: 'Labor Disruption Risk',        value: 'Low',               trend: 'stable', severity: 'low'  },
    ],

    riskDirection: 'Stable',

    radarDimensions: {
      geography:    72,
      industry:     70,
      logistics:    62,
      concentration: 71,
      volatility:   58,
      fragility:    58,
    },
  },

  samsungSDI: {
    id: 'samsungSDI',
    name: 'Samsung SDI',
    ticker: '006400',
    industry: 'Battery / Energy',
    hq: 'South Korea',
    overallRiskScore: 58,
    riskLevel: 'Medium',
    dependencyExposure: 63,

    riskTrend: [
      { month: 'Apr', score: 55 },
      { month: 'May', score: 54 },
      { month: 'Jun', score: 57 },
      { month: 'Jul', score: 58 },
      { month: 'Aug', score: 56 },
      { month: 'Sep', score: 60 },
      { month: 'Oct', score: 59 },
      { month: 'Nov', score: 57 },
      { month: 'Dec', score: 56 },
      { month: 'Jan', score: 58 },
      { month: 'Feb', score: 59 },
      { month: 'Mar', score: 58 },
    ],

    industryExposure: [
      { industry: 'Lithium Mining',         tier: 'T3', exposure: 32, riskLevel: 'High' },
      { industry: 'Cobalt Processing',      tier: 'T3', exposure: 26, riskLevel: 'High' },
      { industry: 'Cathode Manufacturing',  tier: 'T2', exposure: 22, riskLevel: 'Medium' },
      { industry: 'Nickel Refining',        tier: 'T3', exposure: 12, riskLevel: 'Medium' },
      { industry: 'Logistics & Freight',    tier: 'T2', exposure:  8, riskLevel: 'Low' },
    ],

    tierSplit: { tier2: 38, tier3: 62 },

    riskDimensions: [
      { dimension: 'Geography', tier2: 52, tier3: 78 },
      { dimension: 'Industry',  tier2: 64, tier3: 72 },
      { dimension: 'Logistics', tier2: 48, tier3: 66 },
    ],

    insights: [
      {
        id: 1,
        layer: 'Tier-3',
        dimension: 'Geography',
        severity: 'high',
        text: 'Tier-3 lithium and cobalt sourcing is heavily concentrated in the DRC and South America, regions with elevated political and operational risk.',
      },
      {
        id: 2,
        layer: 'Tier-2',
        dimension: 'Industry',
        severity: 'med',
        text: 'Cathode material manufacturers show moderate geographic diversification but face input pressure from concentrated mineral suppliers.',
      },
      {
        id: 3,
        layer: 'Tier-3',
        dimension: 'Industry',
        severity: 'high',
        text: 'Cobalt processing remains a critical chokepoint — fewer than 5 global processors control the majority of refined cobalt supply.',
      },
    ],

    forecast: [
      { period: 'Mar', actual: 58,   forecast: null, upper: null, lower: null },
      { period: 'Apr', actual: null, forecast: 57,   upper: 61,   lower: 53 },
      { period: 'May', actual: null, forecast: 56,   upper: 61,   lower: 51 },
      { period: 'Jun', actual: null, forecast: 55,   upper: 60,   lower: 50 },
      { period: 'Jul', actual: null, forecast: 56,   upper: 61,   lower: 51 },
      { period: 'Aug', actual: null, forecast: 54,   upper: 59,   lower: 49 },
    ],

    leadingIndicators: [
      { signal: 'Lithium Spot Price Index',     value: '-14% QoQ',  trend: 'down',   severity: 'low'  },
      { signal: 'DRC Political Stability',      value: '4.2 / 10',  trend: 'stable', severity: 'high' },
      { signal: 'Cobalt Supply Concentration',  value: '0.74 HHI',  trend: 'stable', severity: 'high' },
      { signal: 'EV Demand Surge Signal',       value: '+22% YoY',  trend: 'up',     severity: 'med'  },
      { signal: 'Refinery Capacity Utilization',value: '89%',       trend: 'up',     severity: 'med'  },
    ],

    riskDirection: 'Decreasing',

    radarDimensions: {
      geography:    68,
      industry:     66,
      logistics:    54,
      concentration: 63,
      volatility:   52,
      fragility:    52,
    },
  },

  basf: {
    id: 'basf',
    name: 'BASF',
    ticker: 'BASFY',
    industry: 'Chemicals',
    hq: 'Germany',
    overallRiskScore: 44,
    riskLevel: 'Low',
    dependencyExposure: 48,

    riskTrend: [
      { month: 'Apr', score: 48 },
      { month: 'May', score: 46 },
      { month: 'Jun', score: 47 },
      { month: 'Jul', score: 45 },
      { month: 'Aug', score: 44 },
      { month: 'Sep', score: 43 },
      { month: 'Oct', score: 45 },
      { month: 'Nov', score: 44 },
      { month: 'Dec', score: 43 },
      { month: 'Jan', score: 44 },
      { month: 'Feb', score: 45 },
      { month: 'Mar', score: 44 },
    ],

    industryExposure: [
      { industry: 'Natural Gas Extraction',  tier: 'T2', exposure: 28, riskLevel: 'Medium' },
      { industry: 'Petrochemical Refining',  tier: 'T2', exposure: 25, riskLevel: 'Medium' },
      { industry: 'Mineral Mining',          tier: 'T3', exposure: 22, riskLevel: 'Low' },
      { industry: 'Water Treatment',         tier: 'T3', exposure: 14, riskLevel: 'Low' },
      { industry: 'Logistics & Freight',     tier: 'T2', exposure: 11, riskLevel: 'Low' },
    ],

    tierSplit: { tier2: 61, tier3: 39 },

    riskDimensions: [
      { dimension: 'Geography', tier2: 44, tier3: 52 },
      { dimension: 'Industry',  tier2: 48, tier3: 40 },
      { dimension: 'Logistics', tier2: 38, tier3: 35 },
    ],

    insights: [
      {
        id: 1,
        layer: 'Tier-2',
        dimension: 'Geography',
        severity: 'low',
        text: 'Tier-2 natural gas inputs are sourced from a diversified set of European and Middle Eastern providers, mitigating single-region dependency.',
      },
      {
        id: 2,
        layer: 'Tier-3',
        dimension: 'Geography',
        severity: 'low',
        text: 'Tier-3 mineral sourcing includes moderate exposure to African extraction sites, though supplier diversification reduces concentration risk.',
      },
      {
        id: 3,
        layer: 'Tier-2',
        dimension: 'Logistics',
        severity: 'low',
        text: 'BASF benefits from proximity to major European logistics corridors, providing resilient routing options relative to APAC-heavy peers.',
      },
    ],

    forecast: [
      { period: 'Mar', actual: 44,   forecast: null, upper: null, lower: null },
      { period: 'Apr', actual: null, forecast: 44,   upper: 48,   lower: 40 },
      { period: 'May', actual: null, forecast: 43,   upper: 47,   lower: 39 },
      { period: 'Jun', actual: null, forecast: 43,   upper: 47,   lower: 39 },
      { period: 'Jul', actual: null, forecast: 42,   upper: 46,   lower: 38 },
      { period: 'Aug', actual: null, forecast: 42,   upper: 46,   lower: 38 },
    ],

    leadingIndicators: [
      { signal: 'European Energy Price Index',    value: '+6% QoQ',  trend: 'up',     severity: 'low'  },
      { signal: 'Natural Gas Supply Stability',   value: '7.8 / 10', trend: 'stable', severity: 'low'  },
      { signal: 'EU Regulatory Risk Score',       value: '3.1 / 10', trend: 'stable', severity: 'low'  },
      { signal: 'Logistics Network Resilience',   value: '8.2 / 10', trend: 'up',     severity: 'low'  },
      { signal: 'Supplier Diversification Index', value: '0.34 HHI', trend: 'stable', severity: 'low'  },
    ],

    riskDirection: 'Stable',

    radarDimensions: {
      geography:    48,
      industry:     46,
      logistics:    36,
      concentration: 48,
      volatility:   42,
      fragility:    28,
    },
  },
}

export const vendorList = Object.values(vendors)
