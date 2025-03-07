if [ ! -n "$ZSH_VERSION" ]; then
  echo "zsh expected"
  return
fi

alias update-proxy-config="sudo python ~/Repos/env/proxy/update-config.py"

# alias push-lineageos-update="~/Repos/env/push-lineageos-update.sh"
alias push-lineageos-update="~/Repos/lineage-nio/packages/apps/Updater/push-update.sh"

readonly TO_BE_REPLACED_BUILTINS=('echo' 'kill' 'printf' 'pwd' 'test')
for i in $TO_BE_REPLACED_BUILTINS
do
  alias "$i=/usr/bin/$i"
done

export TIMEFMT="Time: %U(user) %S(system) %E(elapsed) %P(CPU)
Memory: (%Xavgtext+%Davgdata %Mmaxresident)M
I/O: %Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"

export http_proxy="http://127.0.0.1:1080"
export https_proxy="http://127.0.0.1:1080"

export VISUAL=vim

fpath=(/usr/lib/python3.11/site-packages/argcomplete/bash_completion.d "${fpath[@]}")

# env-modules
. /etc/modules/init/zsh
ml use "$HOME/.local/share/modulefiles"
