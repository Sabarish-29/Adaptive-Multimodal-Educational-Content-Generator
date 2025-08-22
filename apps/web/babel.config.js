module.exports = {
  presets: [
    ['next/babel'],
    ['@babel/preset-typescript', { allowDeclareFields: true }]
  ],
  plugins: [
    ['@babel/plugin-transform-class-properties', { loose: true }],
  ['@babel/plugin-transform-private-methods', { loose: true }],
  // Added to align loose mode across related proposals and silence warnings
  ['@babel/plugin-transform-private-property-in-object', { loose: true }]
  ]
};
