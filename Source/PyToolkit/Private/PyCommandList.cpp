
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

TSharedPtr<FJsonObject> FPyCommandList::ReadJson(const FString path){
	FString jsonValue;
    bool flag = FFileHelper::LoadFileToString(jsonValue, *path);

   //将json转换为结构体
    TSharedRef<TJsonReader<TCHAR>> JsonReader = TJsonReaderFactory<TCHAR>::Create(jsonValue);
    TSharedPtr<FJsonObject> JsonObject;
    bool BFlag = FJsonSerializer::Deserialize(JsonReader, JsonObject);
    if (BFlag)
    {
        return JsonObject;
    }
	return nullptr;
}

void FPyCommandList::ExtendSequencerMenuEntry(FString Script)
{
	// Add Sequncer Menu
	ISequencerModule& SequencerModule = FModuleManager::Get().LoadModuleChecked<ISequencerModule>("Sequencer");
	TSharedPtr<FExtensibilityManager> Manager = SequencerModule.GetObjectBindingContextMenuExtensibilityManager();
	TSharedPtr<FExtender> MenuExtender = MakeShareable(new FExtender);
	
	static FString _Script = Script;
	struct Callback
	{	
		static void RunCommand() {
			GEngine->Exec(NULL, _Script.GetCharArray().GetData());
		}
		static void ExtendMenu(FMenuBuilder& MenuBuilder)
		{
			// TODO if the actor dosn't contian certain component , skip it 
			MenuBuilder.BeginSection("FXCurve", LOCTEXT("FXCurve", "FXCurve"));
			{
				FUIAction Action(FExecuteAction::CreateStatic(&RunCommand));

				MenuBuilder.AddMenuEntry(
					LOCTEXT("ExportCurve", "Export Curve"),
					LOCTEXT("ExportCurveTooltip", "Export Curve to FX Blueprint"),
					FSlateIcon(),
					Action);
			}
			MenuBuilder.EndSection();
		}
	};

	MenuExtender->AddMenuExtension(
		TEXT("Spawnable"),
		EExtensionHook::Before,
		TSharedPtr<FUICommandList>(),
		FMenuExtensionDelegate::CreateStatic(&Callback::ExtendMenu)
	);
	Manager->AddExtender(MenuExtender);

}
#undef LOCTEXT_NAMESPACE
