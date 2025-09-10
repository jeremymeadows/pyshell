{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    fortune
    cowsay
    lolcat
    python312
    (python312.withPackages(p: with p; [
      docker
    ]))
  ];
  shellHook = ''
    exec python -m pyshell
  '';
}
