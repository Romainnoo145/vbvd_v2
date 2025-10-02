"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ExternalLink, Maximize2 } from "lucide-react";

interface IIIFViewerProps {
  manifestUrl: string;
  artworkTitle: string;
  artistName: string;
  trigger?: React.ReactNode;
}

export function IIIFViewer({ manifestUrl, artworkTitle, artistName, trigger }: IIIFViewerProps) {
  const [open, setOpen] = useState(false);

  // Use Universal Viewer which can load any IIIF manifest
  const viewerUrl = `https://universalviewer.io/uv.html?manifest=${encodeURIComponent(manifestUrl)}`;

  return (
    <>
      {trigger ? (
        <div onClick={() => setOpen(true)}>{trigger}</div>
      ) : (
        <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
          <Maximize2 className="mr-2 h-4 w-4" />
          View IIIF
        </Button>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-6xl h-[90vh]">
          <DialogHeader>
            <DialogTitle>{artworkTitle}</DialogTitle>
            <DialogDescription>{artistName}</DialogDescription>
          </DialogHeader>
          <div className="flex-1 relative h-full">
            <iframe
              src={viewerUrl}
              className="w-full h-full border-0 rounded"
              title={`IIIF Viewer: ${artworkTitle}`}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" asChild>
              <a href={viewerUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Open in New Tab
              </a>
            </Button>
            <Button variant="outline" asChild>
              <a href={manifestUrl} target="_blank" rel="noopener noreferrer">
                View Manifest
              </a>
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
