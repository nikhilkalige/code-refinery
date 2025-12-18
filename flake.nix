{
  description = "Competitive programming";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/25.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
        pythonPackages = python.pkgs;

        mkScript = name: text: pkgs.writeScriptBin name text;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = let 
            kattis = mkScript "kattis" ''
              gitroot=$(git rev-parse --show-toplevel)
              $gitroot/kattis/kattis.py "$@"
            '';
          in
            [
              kattis
              python
              pythonPackages.requests
            ];

          shellHook = ''
            echo "Python version: $(python --version)"
          '';
        };
      }
    );
}
