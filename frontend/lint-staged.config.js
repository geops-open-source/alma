/**
 * @filename: lint-staged.config.js
 * @type {import('lint-staged').Configuration}
 */
module.exports = {
  "**/*.ts?(x)": (filenames) => {
    return [
      `eslint --fix .${filenames
        .map((file) => {
          return file.split(process.cwd())[1];
        })
        .join(" .")}`,
      `prettier --write ${filenames.join(" ")}`,
      "tsc -p tsconfig.json --noEmit",
    ];
  },
};
