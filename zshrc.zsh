if [ ! -n "$ZSH_VERSION" ]; then
  echo "zsh expected"
  return
fi

alias update-sing-box-config="(cat ~/Repos/env/proxy/sing-box/update-config.py | sudo python)"

disable kill
disable printf

export TIMEFMT="Time: %U(user) %S(system) %E(elapsed) %P(CPU)
Memory: (%Xavgtext+%Davgdata %Mmaxresident)M
I/O: %Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"
