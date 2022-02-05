if [ ! -n "$ZSH_VERSION" ]; then
  echo "zsh expected"
  return
fi

alias update-p10k="git -C ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k pull"

alias baidunetdisk="sandbox ~/Documents/Sandbox/BaiduNetdisk --bind ~/Downloads/BaiduNetdisk/ ~/Downloads -- /usr/bin/baidunetdisk"
alias malody="sandbox ~/Documents/Sandbox/Malody -- /usr/bin/wine ~/Malody-4.3.7/malody.exe"
alias wemeet="sandbox ~/Documents/Sandbox/WeMeet -- sh -c '/opt/apps/com.tencent.meeting.deepin/files/run.sh && sleep infinity'"
alias xes="sandbox ~/Documents/Sandbox/XES -- wine 'C:\Program Files (x86)\xeszx\3.20.0.1655\owcrclient.exe'"

disable kill
disable printf

export TIMEFMT="Time: %U(user) %S(system) %E(elapsed) %P(CPU)
Memory: (%Xavgtext+%Davgdata %Mmaxresident)M
I/O: %Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"
