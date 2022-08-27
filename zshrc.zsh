if [ ! -n "$ZSH_VERSION" ]; then
  echo "zsh expected"
  return
fi

alias update-sub="sudo -u clash /home/clash/update-sub.py && sudo systemctl restart clash@clash"

# alias baidunetdisk="sandbox ~/Documents/Sandbox/BaiduNetdisk --bind ~/Downloads/BaiduNetdisk/ ~/Downloads -- /usr/bin/baidunetdisk"
# alias malody="sandbox ~/Documents/Sandbox/Malody -- /usr/bin/wine ~/Malody-4.3.7/malody.exe"
# alias xes="sandbox ~/Documents/Sandbox/XES --tmpfs ~/.wine/drive_c/users/zhr/AppData/Local/owcrclient/wcropenclassroom/dump/ -- wine 'C:\\Program Files (x86)\\xeszx\\3.24.0.1755\\owcrclient.exe'"

disable kill
disable printf

export TIMEFMT="Time: %U(user) %S(system) %E(elapsed) %P(CPU)
Memory: (%Xavgtext+%Davgdata %Mmaxresident)M
I/O: %Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"
