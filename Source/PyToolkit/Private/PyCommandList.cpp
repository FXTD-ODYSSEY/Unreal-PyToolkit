
#include "PyCommandList.h"

// PyCommandList

#define LOCTEXT_NAMESPACE "FPyCommandList"

FPyCommandList::FPyCommandList() : TCommands<FPyCommandList>(
	"PyToolkitCommands",
	LOCTEXT("PyToolkitCommands", "PyToolkit CommandList"),
	//NSLOCTEXT("Contexts", "PyToolkitCommands", "PyToolkit CommandList"),
	NAME_None, 
	FEditorStyle::GetStyleSetName())
{
}

void FPyCommandList::RegisterCommands()
{

	UI_COMMAND(OpenLauncher, "Launcher", "Open Qt Launcher", EUserInterfaceActionType::Button, FInputChord(EModifierKey::Control, EKeys::F));

}

#undef LOCTEXT_NAMESPACE
